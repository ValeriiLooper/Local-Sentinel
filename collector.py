import logging
from telethon import TelegramClient, events
from datetime import datetime, timezone
from config import API_ID, API_HASH, SESSION_NAME, SOURCE_CHANNELS, KEYWORDS, STOP_WORDS, IGNORE_OLD_MESSAGES
from database import save_message, is_banned, init_db

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(r"C:\LocalSentinel\logs_collector.txt"),
        logging.StreamHandler()
    ]
)

# Start time for "Ignore Old Messages" logic
START_TIME = datetime.now(timezone.utc)

# Initialize Client
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

def contains_keywords(text: str) -> bool:
    """Checks if the text contains any of the target keywords."""
    if not text:
        return False
    text_lower = text.lower()
    return any(word.lower() in text_lower for word in KEYWORDS)

def has_stop_words(text: str) -> bool:
    """Checks if the text contains any prohibited stop words."""
    if not text:
        return False
    text_lower = text.lower()
    return any(word.lower() in text_lower for word in STOP_WORDS)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def message_handler(event):
    """
    Core logic for intercepting and filtering messages.
    """
    # {Calc_Logic}: Skip messages sent before the script started
    if IGNORE_OLD_MESSAGES and event.message.date < START_TIME:
        return

    sender = await event.get_sender()
    author_id = event.sender_id
    username = getattr(sender, 'username', 'Unknown')
    text = event.raw_text
    chat_title = getattr(event.chat, 'title', 'Private/Unknown Chat')

    # 1. Check Blacklist
    if is_banned(author_id):
        logging.info(f"Skipped message from banned user: {author_id}")
        return

    # 2. Check Stop Words
    if has_stop_words(text):
        logging.info(f"Message from {chat_title} contains stop words. Ignored.")
        return

    # 3. Keyword Match
    if contains_keywords(text):
        # 4. Attempt to save in DB (Deduplication happens here)
        success = save_message(
            source=chat_title,
            author_id=author_id,
            username=username,
            content=text
        )
        
        if success:
            logging.info(f"New Match Found! Source: {chat_title} | Author: {username}")
        else:
            logging.info(f"Duplicate message ignored: {chat_title}")

async def main():
    # Ensure DB is ready
    init_db()
    
    logging.info("Starting Collector...")
    await client.start()
    logging.info("Collector is running and listening for new messages.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    client.loop.run_until_complete(main())
