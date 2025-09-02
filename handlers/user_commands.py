import logging
import time
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from database import SessionLocal, AdminSettings, User, get_or_create_admin_settings
from shortener import shorten_link
from jobs import remove_member_job

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()

    try:
        # User ko DB me add ya get karna
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            user = User(user_id=user_id)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Naya user database me add hua: {user_id}")

        # Admin settings get karna
        settings = get_or_create_admin_settings(db)
        if not settings.channel_id:
            await update.message.reply_text("⚠️ माफ कीजिए, एडमिन ने अभी तक कोई चैनल सेट नहीं किया है।")
            return

        # Bot ko channel me admin permissions hai ya nahi, check karna
        try:
            bot_member = await context.bot.get_chat_member(settings.channel_id, context.bot.id)
            if not bot_member.status == 'administrator' or not bot_member.can_invite_users or not bot_member.can_restrict_members:
                await update.message.reply_text("⚠️ बॉट को चैनल में एडमिन अधिकार (Invite & Ban) नहीं हैं। कृपया एडमिन से संपर्क करें।")
                return
        except TelegramError as e:
            await update.message.reply_text(f"⚠️ चैनल (`{settings.channel_id}`) को एक्सेस करने में समस्या: {e.message}")
            logger.error(f"Channel access error for {settings.channel_id}: {e}")
            return
            
        # Invite link generate karna
        expire_date = datetime.now() + timedelta(minutes=5) # Link 5 minute me expire ho jayega
        invite_link_obj = await context.bot.create_chat_invite_link(
            chat_id=settings.channel_id,
            expire_date=expire_date,
            member_limit=1
        )
        invite_link = invite_link_obj.invite_link
        
        duration_seconds = settings.invite_duration_seconds
        
        # User ko link dena
        if not user.has_received_free_link:
            # Pehli baar: Free link
            user.has_received_free_link = True
            
            keyboard = [[InlineKeyboardButton("🔗 चैनल ज्वाइन करें (Free)", url=invite_link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "🎉 आपका फ्री चैनल एक्सेस लिंक यहाँ है! यह लिंक केवल आपके लिए है और कुछ समय में समाप्त हो जाएगा।",
                reply_markup=reply_markup
            )
        else:
            # Dusri baar: Shortened link
            if not settings.shortener_domain or not settings.shortener_api:
                await update.message.reply_text("⚠️ माफ कीजिए, एडमिन ने अभी तक shortener service सेट नहीं की है।")
                return

            await update.message.reply_text("⏳ आपका लिंक तैयार किया जा रहा है, कृपया प्रतीक्षा करें...")
            
            shortened_link = await shorten_link(settings.shortener_domain, settings.shortener_api, invite_link)
            
            if shortened_link:
                keyboard = [[InlineKeyboardButton("🔗 विज्ञापन देखें और चैनल ज्वाइन करें", url=shortened_link)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "यह रहा आपका लिंक। चैनल ज्वाइन करने के लिए कृपया विज्ञापन देखें।",
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text("❌ लिंक बनाने में कोई त्रुटि हुई। कृपया बाद में प्रयास करें।")
                return # Job schedule nahi karna agar link fail ho gaya

        # User ko remove karne ke liye job schedule karna
        context.job_queue.run_once(
            remove_member_job,
            when=duration_seconds,
            data={"user_id": user_id, "channel_id": settings.channel_id},
            name=f"remove_{user_id}_{settings.channel_id}"
        )
        
        user.last_link_timestamp = time.time()
        db.commit()
        
        logger.info(f"User {user_id} ke liye {duration_seconds}s ka removal job schedule kiya gaya.")

    except Exception as e:
        logger.error(f"Start command me error: {e}", exc_info=True)
        await update.message.reply_text("🤖 कुछ आंतरिक त्रुटि हुई है। कृपया एडमिन से संपर्क करें।")
    finally:
        db.close()
