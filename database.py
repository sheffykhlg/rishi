import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config import MONGO_URI

logger = logging.getLogger(__name__)

# --- MongoDB Client Setup ---
try:
    client = MongoClient(MONGO_URI)
    # The ismaster command is cheap and does not require auth. Used to check connection.
    client.admin.command('ismaster')
    logger.info("Successfully connected to MongoDB.")
except ConnectionFailure as e:
    logger.error(f"Could not connect to MongoDB: {e}")
    # You might want to exit the bot if DB connection fails
    raise

# Define the database and collections
db = client.get_database("TelegramBotDB") # You can change the database name if you want
admin_settings = db.get_collection("admin_settings")
users_collection = db.get_collection("users")

# Helper function to get or create the admin settings document
def get_admin_settings():
    """
    Retrieves the admin settings document. If it doesn't exist, it creates one with default values.
    """
    settings = admin_settings.find_one({"_id": 1})
    if not settings:
        # Create default settings if none exist
        default_settings = {
            "_id": 1,
            "channel_id": None,
            "shortener_api": None,
            "shortener_domain": None,
            "invite_duration_seconds": 86400  # Default: 1 day in seconds
        }
        admin_settings.insert_one(default_settings)
        return default_settings
    return settings
