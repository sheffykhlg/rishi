import logging
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

async def remove_member_job(context):
    """JobQueue dwara call kiya jane wala function, user ko channel se remove karne ke liye."""
    job_context = context.job.data
    user_id = job_context["user_id"]
    channel_id = job_context["channel_id"]
    
    logger.info(f"User {user_id} ko channel {channel_id} se remove karne ka samay aa gaya hai.")
    
    try:
        # User ko kick karna (ban karna)
        await context.bot.ban_chat_member(chat_id=channel_id, user_id=user_id)
        # Turant unban karna taki woh future me dobara join kar sake
        await context.bot.unban_chat_member(chat_id=channel_id, user_id=user_id)
        
        logger.info(f"User {user_id} ko channel {channel_id} se safaltapurvak remove kar diya gaya.")
        
        # Aap yahan user ko ek notification bhej sakte hain
        await context.bot.send_message(
            chat_id=user_id,
            text="Aapka channel access time poora ho gaya hai. Dobara join karne ke liye /start use karein."
        )

    except TelegramError as e:
        logger.error(f"User {user_id} ko channel {channel_id} se remove karne me error: {e}")
    except Exception as e:
        logger.error(f"Remove job me anumanit error: {e}")
