import os
import threading
from flask import Flask
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream # Naya Import v4 ke liye

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING")

# Groups aur Admins
allowed_groups_env = os.environ.get("ALLOWED_GROUPS", "")
ALLOWED_GROUPS = [int(x.strip()) for x in allowed_groups_env.split(",") if x.strip()]

authorized_users_env = os.environ.get("AUTHORIZED_USERS", "")
AUTHORIZED_USERS = [int(x.strip()) for x in authorized_users_env.split(",") if x.strip()]

# --- FLASK SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running (Latest Engine)!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- BOT SETUP ---
user_bot = Client(
    "glitch_shield", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    session_string=SESSION
)

call_py = PyTgCalls(user_bot)

# --- PERMISSIONS ---
async def is_authorized(message):
    if message.chat.id not in ALLOWED_GROUPS:
        return False
    if message.from_user and message.from_user.id in AUTHORIZED_USERS:
        return True
    if message.sender_chat and message.sender_chat.id == message.chat.id:
        return True
    return False

# --- COMMANDS ---
@user_bot.on_message(filters.command(["ten_join", "join"], prefixes=["/", "!"]) & filters.group)
async def join_vc(client, message):
    if not await is_authorized(message):
        return

    chat_id = message.chat.id
    try:
        await message.reply("🛡️ Shield Activating (Auto-Version)...")
        
        # Latest Syntax: play() use karte hain ab
        await call_py.play(
            chat_id, 
            MediaStream(
                "http://docs.evostream.com/sample_content/assets/sintel1min720p.mkv"
            )
        )
        await message.reply("✅ **Shield Active!**\nLatest Engine Connected.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

@user_bot.on_message(filters.command(["ten_leave", "leave"], prefixes=["/", "!"]) & filters.group)
async def leave_vc(client, message):
    if not await is_authorized(message):
        return

    chat_id = message.chat.id
    try:
        await call_py.leave_call(chat_id)
        await message.reply("👋 Shield Deactivated.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# --- STARTUP ---
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    call_py.start()
    user_bot.run()
