import sqlite3
import hashlib
from datetime import datetime
from config import DB_PATH

def init_db():
    """Initializes the database and creates necessary tables."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Enable WAL mode for concurrent access
        cursor.execute("PRAGMA journal_mode=WAL;")
        
        # Table for messages awaiting moderation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT,
                author_id INTEGER,
                username TEXT,
                content TEXT,
                msg_hash TEXT UNIQUE,
                status TEXT DEFAULT 'pending',
                created_at DATETIME
            )
        ''')
        
        # Table for blacklisted users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blacklist (
                user_id INTEGER PRIMARY KEY,
                reason TEXT,
                added_at DATETIME
            )
        ''')
        conn.commit()

def generate_hash(text: str) -> str:
    """Generates a unique hash for text to prevent duplicates."""
    return hashlib.md5(text.strip().lower().encode()).hexdigest()

def is_banned(user_id: int) -> bool:
    """Checks if a user is in the blacklist."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM blacklist WHERE user_id = ?", (user_id,))
        return cursor.fetchone() is not None

def add_to_blacklist(user_id: int, reason: str = "Manual ban"):
    """Adds a user to the blacklist."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO blacklist (user_id, reason, added_at) VALUES (?, ?, ?)",
                           (user_id, reason, datetime.now()))
            conn.commit()
    except Exception as e:
        print(f"[Error] Failed to blacklist user: {e}")

def save_message(source, author_id, username, content):
    """Saves a filtered message to the database if it's not a duplicate."""
    msg_hash = generate_hash(content)
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO messages (source_id, author_id, username, content, msg_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (str(source), author_id, username, content, msg_hash, datetime.now()))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        # {Calc_Logic}: Duplicate found via msg_hash unique constraint
        return False

# Initialize DB when script is run
if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
