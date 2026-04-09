import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import MOD_BOT_TOKEN, PUB_BOT_TOKEN, ADMIN_ID, TARGET_CHANNEL_ID, DB_PATH
from database import add_to_blacklist

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Initialize Bots
mod_bot = Bot(token=MOD_BOT_TOKEN)
pub_bot = Bot(token=PUB_BOT_TOKEN)
dp = Dispatcher()

# --- FSM States ---
class EditStates(StatesGroup):
    editing_text = State()

# --- Database Helpers ---
def get_pending_message():
    """Fetches one message that needs moderation."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, source_id, username, content FROM messages WHERE status = 'pending' LIMIT 1")
        return cursor.fetchone()

def update_message_status(msg_id, status, new_content=None):
    """Updates status and optionally the text of a message."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        if new_content:
            cursor.execute("UPDATE messages SET status = ?, content = ? WHERE id = ?", (status, new_content, msg_id))
        else:
            cursor.execute("UPDATE messages SET status = ? WHERE id = ?", (status, msg_id))
        conn.commit()

# --- Keyboards ---
def get_mod_keyboard(msg_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Post", callback_data=f"post_{msg_id}"),
        InlineKeyboardButton(text="📝 Edit", callback_data=f"edit_{msg_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🚫 Ban Author", callback_data=f"ban_{msg_id}"),
        InlineKeyboardButton(text="📁 Archive", callback_data=f"arc_{msg_id}")
    )
    return builder.as_markup()

# --- Handlers ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Sentinel Moderator Bot is active. Checking for new messages...")

# Polling loop for new messages
async def check_for_new_data():
    """{Calc_Logic}: Periodically checks DB for new entries to notify admin."""
    while True:
        data = get_pending_message()
        if data:
            msg_id, source, author, content = data
            text = f"📍 **Source:** {source}\n👤 **Author:** {author}\n\n📝 **Content:**\n{content}"
            await mod_bot.send_message(ADMIN_ID, text, reply_markup=get_mod_keyboard(msg_id), parse_mode="Markdown")
            # Set to 'notified' to avoid spamming the same message in loop
            update_message_status(msg_id, 'notified')
        await asyncio.sleep(5) # Check every 5 seconds

# Callback handlers
@dp.callback_query(F.data.startswith("post_"))
async def handle_post(callback: types.Callback_query):
    msg_id = int(callback.data.split("_")[1])
    with sqlite3.connect(DB_PATH) as conn:
        content = conn.execute("SELECT content FROM messages WHERE id = ?", (msg_id,)).fetchone()[0]
    
    await pub_bot.send_message(TARGET_CHANNEL_ID, content)
    update_message_status(msg_id, 'approved')
    await callback.message.edit_text(f"✅ **Published to channel**\n\n{content}")

@dp.callback_query(F.data.startswith("ban_"))
async def handle_ban(callback: types.Callback_query):
    msg_id = int(callback.data.split("_")[1])
    with sqlite3.connect(DB_PATH) as conn:
        author_id = conn.execute("SELECT author_id FROM messages WHERE id = ?", (msg_id,)).fetchone()[0]
    
    add_to_blacklist(author_id)
    update_message_status(msg_id, 'banned')
    await callback.message.edit_text("🚫 **User blacklisted and message removed.**")

@dp.callback_query(F.data.startswith("edit_"))
async def handle_edit_request(callback: types.Callback_query, state: FSMContext):
    msg_id = int(callback.data.split("_")[1])
    await state.update_data(editing_id=msg_id)
    await state.set_state(EditStates.editing_text)
    await callback.message.answer("Please send the corrected text for this post:")

@dp.message(EditStates.editing_text)
async def process_new_text(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    msg_id = user_data['editing_id']
    new_text = message.text
    
    update_message_status(msg_id, 'pending', new_content=new_text)
    await state.clear()
    await message.answer("Text updated. It will appear for moderation again shortly.")

# --- Main ---
async def main():
    # Start checking loop in background
    asyncio.create_task(check_for_new_data())
    # Start bot polling
    await dp.start_polling(mod_bot)

if __name__ == "__main__":
    asyncio.run(main())
