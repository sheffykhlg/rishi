import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, JobQueue, ChatMemberHandler

# Import variables from the config file
from config import BOT_TOKEN

# Import command handlers
from handlers.user_commands import start, help_command, track_joins
from handlers.admin_commands import (
    set_channel, my_set_channel, set_domain, set_api, set_time, stats, broadcast, delete_all_settings
)

# Set up basic logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def main() -> None:
    """
    The main function to set up and run the bot.
    """
    
    logger.info("Building bot application...")
    
    # Explicitly create the JobQueue
    job_queue = JobQueue()
    
    # Build the application and set longer timeouts and the job queue
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30)  # Timeout increased to 30 seconds
        .read_timeout(30)     # Timeout increased to 30 seconds
        .job_queue(job_queue)
        .build()
    )

    # --- Register User Command Handlers ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # --- Register Admin Command Handlers ---
    application.add_handler(CommandHandler("setch", set_channel))
    application.add_handler(CommandHandler("mysetch", my_set_channel))
    application.add_handler(CommandHandler("setdomain", set_domain))
    application.add_handler(CommandHandler("setapi", set_api))
    application.add_handler(CommandHandler("settime", set_time))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("dltall", delete_all_settings))

    # --- Register the join tracker handler ---
    application.add_handler(ChatMemberHandler(track_joins, ChatMemberHandler.CHAT_MEMBER))

    logger.info("Starting bot polling...")
    
    # The application.run_polling() method automatically starts the job queue.
    # We do NOT need to call application.job_queue.start() manually.
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
