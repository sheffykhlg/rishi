import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config import MONGO_URI

logger = logging.getLogger(__name__)

# MongoDB Client Setup
try:
    client = MongoClient(MONGO_URI)
    # The ismaster command is cheap and does not require auth.
    client.admin.command('ismaster')
    logger.info("MongoDB se safaltapurvak connect ho gaya.")
except ConnectionFailure as e:
    logger.error(f"MongoDB se connect nahi ho paya: {e}")
    # Aap yahan bot ko exit karna bhi choose kar sakte hain
    # exit() 
    raise

# Database aur Collections ko define karna
db = client.get_database("TelegramBotDB") # Aap database ka naam badal sakte hain
admin_settings = db.get_collection("admin_settings")
users_collection = db.get_collection("users")

# Helper function jo admin settings ko get ya create karega
def get_admin_settings():
    """Admin settings document ko get ya create karta hai."""
    settings = admin_settings.find_one({"_id": 1})
    if not settings:
        # Default settings create karna
        default_settings = {
            "_id": 1,
            "channel_id": None,
            "shortener_api": None,
            "shortener_domain": None,
            "invite_duration_seconds": 86400  # Default: 1 din
        }
        admin_settings.insert_one(default_settings)
        return default_settings
    return settings

