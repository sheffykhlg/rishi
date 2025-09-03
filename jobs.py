import logging
from telegram.ext import ContextTypes
from telegram.error import Forbidden, BadRequest

logger = logging.getLogger(__name__)

async def remove_member_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Job function called by the JobQueue to remove a user from the channel.
    """
    job_context = context.job.data
    user_id = job_context["user_id"]
    channel_id = job_context["channel_id"]
    
    logger.info(f"Attempting to remove user {user_id} from channel {channel_id}.")
    
    try:
        # Kick (ban) the user to remove them from the channel
        await context.bot.ban_chat_member(chat_id=channel_id, user_id=user_id)
        
        # Immediately unban the user so they can rejoin later with a new link
        await context.bot.unban_chat_member(chat_id=channel_id, user_id=user_id)
        
        logger.info(f"Successfully removed user {user_id} from channel {channel_id}.")
        
        # Optionally, notify the user that their access has expired
        await context.bot.send_message(
            chat_id=user_id,
            text="Your access to the channel has expired. Use /start to get a new link."
        )

    except Forbidden:
        logger.error(
            f"Failed to remove user {user_id}. Bot lacks administrator rights "
            f"to ban members in channel {channel_id}."
        )
    except BadRequest as e:
        logger.error(f"Failed to remove user {user_id} from {channel_id}: {e.message}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the remove job for user {user_id}: {e}")
