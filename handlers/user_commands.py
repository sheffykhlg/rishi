import logging
import time
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from database import admin_settings, users_collection, get_admin_settings
from shortener import shorten_link
from jobs import remove_member_job
from config import ADMIN_ID

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /start command. Adds user to DB, generates an invite link,
    and schedules their removal.
    """
    user_id = update.effective_user.id

    try:
        # Get or create the user in the database
        user = users_collection.find_one({"_id": user_id})
        if not user:
            users_collection.insert_one({
                "_id": user_id,
                "has_received_free_link": False,
                "last_link_timestamp": None
            })
            user = users_collection.find_one({"_id": user_id})
            logger.info(f"New user added to the database: {user_id}")

        # Get admin settings
        settings = get_admin_settings()
        channel_id = settings.get("channel_id")

        if not channel_id:
            await update.message.reply_text("⚠️ Sorry, the admin has not configured a channel yet.")
            return

        # Check if the bot has the necessary permissions in the channel
        try:
            bot_member = await context.bot.get_chat_member(channel_id, context.bot.id)
            if not bot_member.status == 'administrator' or not bot_member.can_invite_users or not bot_member.can_restrict_members:
                await update.message.reply_text(
                    "⚠️ Bot is missing Admin permissions (Invite & Ban) in the channel. Please contact the admin."
                )
                return
        except TelegramError as e:
            await update.message.reply_text(f"⚠️ Could not access the channel (`{channel_id}`): {e.message}")
            logger.error(f"Channel access error for {channel_id}: {e}")
            return
            
        # Generate a new, single-use invite link valid for 10 minutes
        expire_date = datetime.now() + timedelta(minutes=10)
        invite_link_obj = await context.bot.create_chat_invite_link(
            chat_id=channel_id,
            expire_date=expire_date,
            member_limit=1
        )
        invite_link = invite_link_obj.invite_link
        
        duration_seconds = settings.get("invite_duration_seconds", 86400)
        
        # Decide whether to give a free link or a shortened link
        if not user.get("has_received_free_link"):
            # First time user gets a free link
            update_data = {"$set": {"has_received_free_link": True, "last_link_timestamp": time.time()}}
            keyboard = [[InlineKeyboardButton("🔗 Join Channel (Free Access)", url=invite_link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "🎉 Here is your free access link! It is valid for one use and will expire in 10 minutes.",
                reply_markup=reply_markup
            )
        else:
            # Returning user gets a shortened link
            shortener_domain = settings.get("shortener_domain")
            shortener_api = settings.get("shortener_api")
            
            if not shortener_domain or not shortener_api:
                await update.message.reply_text("⚠️ Sorry, the shortener service is not configured by the admin yet.")
                return

            await update.message.reply_text("⏳ Please wait, your link is being generated...")
            
            shortened_link = await shorten_link(shortener_domain, shortener_api, invite_link)
            
            if shortened_link:
                keyboard = [[InlineKeyboardButton("🔗 Watch Ad & Join Channel", url=shortened_link)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "Here is your new link. Please watch the ad to join the channel.",
                    reply_markup=reply_markup
                )
                update_data = {"$set": {"last_link_timestamp": time.time()}}
            else:
                await update.message.reply_text("❌ An error occurred while creating the link. Please try again later.")
                return

        # Schedule the job to remove the user after the specified duration
        context.job_queue.run_once(
            remove_member_job,
            when=duration_seconds,
            data={"user_id": user_id, "channel_id": channel_id},
            name=f"remove_{user_id}_{channel_id}"
        )
        
        users_collection.update_one({"_id": user_id}, update_data)
        logger.info(f"Scheduled removal job for user {user_id} in {duration_seconds} seconds.")

    except Exception as e:
        logger.error(f"Error in /start command for user {user_id}: {e}", exc_info=True)
        await update.message.reply_text("🤖 An internal error occurred. Please contact the admin.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Displays a help message with all available commands.
    Shows admin commands only to the admin.
    """
    user_id = update.effective_user.id
    
    # Start with the basic user commands
    help_text = "<b>Here are the available commands:</b>\n\n"
    help_text += "<b><u>For All Users:</u></b>\n"
    help_text += "• /start - Get a new channel invite link.\n"
    help_text += "• /help - Show this help message.\n\n"
    
    # Check if the user is the admin and add admin commands if so
    if user_id == ADMIN_ID:
        help_text += "<b><u>For Admin Only:</u></b>\n"
        help_text += "• /setch `[channel_id]` - Set the target channel ID (e.g., -10012345).\n"
        help_text += "• /mysetch - Check the currently set channel ID.\n"
        help_text += "• /setdomain `[domain]` - Set URL shortener domain (e.g., `example.com`).\n"
        help_text += "• /setapi `[api_key]` - Set the URL shortener API key.\n"
        help_text += "• /settime `[value] [unit]` - Set user access duration (e.g., `/settime 1 d`).\n"
        help_text += "    (Units: s, m, h, d)\n"
        help_text += "• /stats - Get total bot users.\n"
        help_text += "• /broadcast `[message]` - Send a message to all users.\n"
        help_text += "• /dltall - Delete and reset all admin settings.\n"
        
    await update.message.reply_html(help_text)


# --- NEW FUNCTION TO TRACK JOINS ---
async def track_joins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    This handler is called whenever a user's status changes in a chat.
    It checks if a user has joined the configured channel and notifies the admin.
    """
    result = update.chat_member
    if not result:
        return

    user = result.new_chat_member.user
    chat_id = result.chat.id
    
    # Get the channel ID configured by the admin
    settings = get_admin_settings()
    admin_channel_id = settings.get("channel_id")

    # Only track joins for the configured channel
    if chat_id != admin_channel_id:
        return

    # Check if the user's status changed from 'not a member' to 'a member'
    was_member = result.old_chat_member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    is_member = result.new_chat_member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]

    if not was_member and is_member:
        logger.info(f"{user.full_name} (ID: {user.id}) joined the channel {chat_id}.")
        
        # Check if this user is a known user of our bot
        bot_user = users_collection.find_one({"_id": user.id})
        
        if bot_user:
            # If they are a known bot user, notify the admin
            notification_message = (
                f"✅ **User Joined Confirmation**\n\n"
                f"👤 **User:** {user.mention_html()}\n"
                f"🆔 **ID:** `{user.id}`\n\n"
                f"They have successfully joined the channel."
            )
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID, text=notification_message, parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Failed to send join notification to admin: {e}")
