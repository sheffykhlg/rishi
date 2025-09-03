import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
import asyncio

from config import ADMIN_ID
from database import admin_settings, users_collection

logger = logging.getLogger(__name__)

# Decorator to restrict a command to the admin only
def admin_only(func):
    """
    A decorator that checks if the user issuing a command is the admin.
    """
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("⛔️ Sorry, this command is for the admin only.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

@admin_only
async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets the target channel ID."""
    try:
        channel_id = int(context.args[0])
        admin_settings.update_one(
            {"_id": 1},
            {"$set": {"channel_id": channel_id}},
            upsert=True
        )
        await update.message.reply_text(f"✅ Channel ID successfully set to `{channel_id}`.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Please use the correct format: `/setch <channel_id>`")

@admin_only
async def my_set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Checks the currently set channel ID."""
    settings = admin_settings.find_one({"_id": 1})
    channel_id = settings.get("channel_id") if settings else None
    if channel_id:
        await update.message.reply_text(f"ℹ️ The current channel ID is: `{channel_id}`")
    else:
        await update.message.reply_text("ℹ️ No channel has been set yet. Use `/setch`.")

@admin_only
async def set_domain(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets the URL shortener domain."""
    try:
        domain = context.args[0]
        admin_settings.update_one(
            {"_id": 1},
            {"$set": {"shortener_domain": domain}},
            upsert=True
        )
        await update.message.reply_text(f"✅ Shortener domain successfully set to `{domain}`.")
    except IndexError:
        await update.message.reply_text("⚠️ Please use the correct format: `/setdomain <domain.com>`")

@admin_only
async def set_api(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets the URL shortener API key."""
    try:
        api_key = context.args[0]
        admin_settings.update_one(
            {"_id": 1},
            {"$set": {"shortener_api": api_key}},
            upsert=True
        )
        await update.message.reply_text("✅ Shortener API key has been set successfully.")
    except IndexError:
        await update.message.reply_text("⚠️ Please use the correct format: `/setapi <api_key>`")

@admin_only
async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets the duration for how long a user stays in the channel."""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ Format: `/settime <number> <unit>`\nUnits: `s`(seconds), `m`(minutes), `h`(hours), `d`(days)"
        )
        return
    try:
        value = int(context.args[0])
        unit = context.args[1].lower()
        
        seconds = 0
        if unit == 's':
            seconds = value
        elif unit == 'm':
            seconds = value * 60
        elif unit == 'h':
            seconds = value * 3600
        elif unit == 'd':
            seconds = value * 86400
        else:
            await update.message.reply_text("⚠️ Invalid unit! Please use `s`, `m`, `h`, or `d`.")
            return

        admin_settings.update_one(
            {"_id": 1},
            {"$set": {"invite_duration_seconds": seconds}},
            upsert=True
        )
        await update.message.reply_text(f"✅ User access duration set to `{value} {unit}` ({seconds} seconds).")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Invalid format! Use `/settime <number> <unit>`.")

@admin_only
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gets the total number of users who have started the bot."""
    user_count = users_collection.count_documents({})
    await update.message.reply_text(f"📊 Total users in the bot: **{user_count}**")

@admin_only
async def delete_all_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deletes and resets all admin settings from the database."""
    try:
        result = admin_settings.delete_one({"_id": 1})
        if result.deleted_count > 0:
            await update.message.reply_text("✅ All admin settings have been successfully deleted.")
            logger.info("Admin settings have been deleted by the admin.")
        else:
            await update.message.reply_text("ℹ️ No settings found to delete.")
    except Exception as e:
        logger.error(f"Error while deleting settings: {e}")
        await update.message.reply_text("❌ An error occurred while deleting settings.")

@admin_only
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Broadcasts a message to all users of the bot."""
    if not context.args:
        await update.message.reply_text("⚠️ Please provide a message to broadcast: `/broadcast <message>`")
        return
    
    message_to_send = " ".join(context.args)
    
    all_users_cursor = users_collection.find({}, {"_id": 1})
    all_user_ids = [user["_id"] for user in all_users_cursor]
    
    if not all_user_ids:
        await update.message.reply_text("There are no users to broadcast to.")
        return

    total_users = len(all_user_ids)
    sent_count = 0
    failed_count = 0
    
    status_message = await update.message.reply_text(f"📣 Starting broadcast... Sent to 0/{total_users}.")
    
    for i, user_id in enumerate(all_user_ids):
        try:
            await context.bot.send_message(chat_id=user_id, text=message_to_send, parse_mode='HTML')
            sent_count += 1
        except Exception as e:
            failed_count += 1
            logger.warning(f"Failed to send broadcast to user {user_id}: {e}")
        
        # Update status message every 10 users or at the end
        if (i + 1) % 10 == 0 or (i + 1) == total_users:
            progress = (i + 1) / total_users
            bar_length = 10
            filled_length = int(bar_length * progress)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            
            try:
                await status_message.edit_text(
                    f"📣 Broadcast in progress...\n`{bar}`\n"
                    f"Sent: {sent_count}/{total_users}\n"
                    f"Failed: {failed_count}",
                    parse_mode='MarkdownV2'
                )
            except Exception:
                pass  # Ignore if editing fails (e.g., message not modified)
        await asyncio.sleep(0.1) # Avoid hitting rate limits

    await status_message.edit_text(
        f"✅ Broadcast complete!\n\n"
        f"Successfully sent: {sent_count}\n"
        f"Failed to send: {failed_count}"
    )
