import os
from dotenv import load_dotenv

# Set working directory
BASE_DIR = r"C:\LocalSentinel"
os.chdir(BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env"))

# --- Telegram Credentials ---
API_ID = int(os.getenv("TELEGRAM_API_ID", 0))
API_HASH = os.getenv("TELEGRAM_API_HASH", "~~~~~~~~~~~~~~~~~")
MOD_BOT_TOKEN = os.getenv("MODERATOR_BOT_TOKEN", "~~~~~~~~~~~~~~~~~")
PUB_BOT_TOKEN = os.getenv("PUBLISHER_BOT_TOKEN", "~~~~~~~~~~~~~~~~~")

# --- IDs ---
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", 0))

# --- Database & Files ---
DB_PATH = os.path.join(BASE_DIR, "sentinel_vault.db")
SESSION_NAME = os.path.join(BASE_DIR, "collector_session")

# --- Monitoring Settings ---
# List of 40 channel IDs or usernames to monitor
SOURCE_CHANNELS = [
    "~~~~~~~~~~~~~~~~~",
    "~~~~~~~~~~~~~~~~~",
    # Add up to 40 sources here
]

# Filtering keywords
KEYWORDS = ["crypto", "news", "urgent", "~~~~~~~~~~~~~~~~~"]
STOP_WORDS = ["scam", "ad", "promo", "~~~~~~~~~~~~~~~~~"]

# {Calc_Logic}: Flag to ignore history on startup
IGNORE_OLD_MESSAGES = True
