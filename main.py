import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, JobQueue

# Config se variables import karna
from config import BOT_TOKEN

# Handlers import karna
from handlers.user_commands import start
from handlers.admin_commands import (
    set_channel, my_set_channel, set_domain, set_api, set_time, stats, broadcast, delete_all_settings
)

# Logging setup karna
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def main() -> None:
    """Bot ko start aur run karta hai."""
    
    logger.info("Bot application banaya ja raha hai...")
    
    # JobQueue (Scheduler) ko explicitly create karna
    job_queue = JobQueue()
    
    # Application builder mein JobQueue ko add karna
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(15)
        .read_timeout(15)
        .job_queue(job_queue)
        .build()
    )

    # User command handlers ko register karna
    application.add_handler(CommandHandler("start", start))

    # Admin command handlers ko register karna
    application.add_handler(CommandHandler("setch", set_channel))
    application.add_handler(CommandHandler("mysetch", my_set_channel))
    application.add_handler(CommandHandler("setdomain", set_domain))
    application.add_handler(CommandHandler("setapi", set_api))
    application.add_handler(CommandHandler("settime", set_time))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("dltall", delete_all_settings))

    logger.info("Bot polling shuru kar raha hai...")
    
    # Bot ko run karne se pehle JobQueue ko start karna
    application.job_queue.start()
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
