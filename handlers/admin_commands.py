import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
import asyncio

from config import ADMIN_ID
from database import admin_settings, users_collection

logger = logging.getLogger(__name__)

# Decorator to check if the user is an admin
def admin_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("⛔️ माफ कीजिए, यह कमांड केवल एडमिन के लिए है।")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

@admin_only
async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        channel_id = int(context.args[0])
        admin_settings.update_one(
            {"_id": 1},
            {"$set": {"channel_id": channel_id}},
            upsert=True
        )
        await update.message.reply_text(f"✅ चैनल ID `{channel_id}` सफलतापूर्वक सेट हो गया है।")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ कृपया सही फॉर्मेट का उपयोग करें: `/setch <channel_id>`")

@admin_only
async def my_set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = admin_settings.find_one({"_id": 1})
    channel_id = settings.get("channel_id") if settings else None
    if channel_id:
        await update.message.reply_text(f"ℹ️ वर्तमान में सेट चैनल ID है: `{channel_id}`")
    else:
        await update.message.reply_text("ℹ️ अभी तक कोई चैनल सेट नहीं किया गया है। `/setch` का उपयोग करें।")

@admin_only
async def set_domain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        domain = context.args[0]
        admin_settings.update_one(
            {"_id": 1},
            {"$set": {"shortener_domain": domain}},
            upsert=True
        )
        await update.message.reply_text(f"✅ Shortener डोमेन `{domain}` सफलतापूर्वक सेट हो गया है।")
    except IndexError:
        await update.message.reply_text("⚠️ कृपया सही फॉर्मेट का उपयोग करें: `/setdomain <domain.com>`")

@admin_only
async def set_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        api_key = context.args[0]
        admin_settings.update_one(
            {"_id": 1},
            {"$set": {"shortener_api": api_key}},
            upsert=True
        )
        await update.message.reply_text("✅ Shortener API की सफलतापूर्वक सेट हो गई है।")
    except IndexError:
        await update.message.reply_text("⚠️ कृपया सही फॉर्मेट का उपयोग करें: `/setapi <api_key>`")

@admin_only
async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("⚠️ फॉर्मेट: `/settime <number> <unit>`\nUnit: `s`, `m`, `h`, `d` (seconds, minutes, hours, days)")
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
            await update.message.reply_text("⚠️ अमान्य यूनिट! कृपया `s`, `m`, `h`, or `d` का उपयोग करें।")
            return

        admin_settings.update_one(
            {"_id": 1},
            {"$set": {"invite_duration_seconds": seconds}},
            upsert=True
        )
        await update.message.reply_text(f"✅ लिंक की वैधता `{value} {unit}` ({seconds} सेकंड) पर सेट कर दी गई है।")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ अमान्य फॉर्मेट! `/settime <number> <unit>` का उपयोग करें।")

@admin_only
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_count = users_collection.count_documents({})
    await update.message.reply_text(f"📊 बॉट के कुल यूजर्स: **{user_count}**")

@admin_only
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ कृपया ब्रॉडकास्ट करने के लिए एक संदेश लिखें: `/broadcast <message>`")
        return
    
    message_to_send = " ".join(context.args)
    
    all_users_cursor = users_collection.find({}, {"_id": 1})
    all_user_ids = [user["_id"] for user in all_users_cursor]
    
    if not all_user_ids:
        await update.message.reply_text("Broadcast करने के लिए कोई यूजर नहीं है।")
        return

    total_users = len(all_user_ids)
    sent_count = 0
    failed_count = 0
    
    status_message = await update.message.reply_text(f"📣 ब्रॉडकास्ट शुरू हो रहा है... 0/{total_users} को भेजा गया।")
    
    for i, user_id in enumerate(all_user_ids):
        try:
            await context.bot.send_message(chat_id=user_id, text=message_to_send, parse_mode='HTML')
            sent_count += 1
        except Exception as e:
            failed_count += 1
            logger.warning(f"User {user_id} को broadcast भेजने में विफल: {e}")
        
        if (i + 1) % 10 == 0 or (i + 1) == total_users:
            progress = (i + 1) / total_users
            bar_length = 10
            filled_length = int(bar_length * progress)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            
            try:
                await status_message.edit_text(
                    f"📣 ब्रॉडकास्ट जारी है...\n`{bar}`\n"
                    f"भेजा गया: {sent_count}/{total_users}\n"
                    f"विफल: {failed_count}",
                    parse_mode='MarkdownV2'
                )
            except Exception:
                pass
        await asyncio.sleep(0.1)

    await status_message.edit_text(
        f"✅ ब्रॉडकास्ट पूरा हुआ!\n\n"
        f"सफलतापूर्वक भेजा गया: {sent_count}\n"
        f"विफल हुए: {failed_count}"
    )
