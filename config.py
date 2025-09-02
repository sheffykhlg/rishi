import os
from dotenv import load_dotenv

# .env file se environment variables load karna
load_dotenv()

# Bot Token ko get karna
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Error: TELEGRAM_BOT_TOKEN environment variable set nahi hai!")

# Admin User ID ko get karna aur integer mein convert karna
try:
    ADMIN_ID = int(os.getenv("ADMIN_USER_ID"))
except (ValueError, TypeError):
    raise ValueError("Error: ADMIN_USER_ID environment variable aek valid integer nahi hai!")
