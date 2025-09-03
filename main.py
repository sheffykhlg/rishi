import logging
from telegram import Update
from telegram.ext import Application, CommandHandler
from telegram.request import Request

# Config se variables import karna
from config import BOT_TOKEN

# Handlers import karna
from handlers.user_commands import start
from handlers.admin_commands import (
    set_channel, my_set_channel, set_domain, set_api, set_time, stats, broadcast
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
    
    # Connection ke liye timeout values set karna
    # Yeh Heroku par "Timed out" error se bachne me madad karega
    request = Request(connect_timeout=10, read_timeout=10)
    
    application = Application.builder().token(BOT_TOKEN).request(request).build()

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

    logger.info("Bot polling shuru kar raha hai...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
