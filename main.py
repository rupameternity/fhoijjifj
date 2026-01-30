import os
import threading
from flask import Flask
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING")

allowed_groups_env = os.environ.get("ALLOWED_GROUPS", "")
ALLOWED_GROUPS = [int(x.strip()) for x in allowed_groups_env.split(",") if x.strip()]

authorized_users_env = os.environ.get("AUTHORIZED_USERS", "")
AUTHORIZED_USERS = [int(x.strip()) for x in authorized_users_env.split(",") if x.strip()]

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

user_bot = Client("glitch_shield", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

async def is_authorized(message):
    if message.chat.id not in ALLOWED_GROUPS: return False
    if message.from_user and message.from_user.id in AUTHORIZED_USERS: return True
    if message.sender_chat and message.sender_chat.id == message.chat.id: return True
    return False

@user_bot.on_message(filters.command(["ten_join", "join"], prefixes=["/", "!"]) & filters.group)
async def join_vc(client, message):
    if not await is_authorized(message): return
    try:
        await message.reply("🛡️ Joining VC...")
        await call_py.play(
            message.chat.id, 
            MediaStream("http://docs.evostream.com/sample_content/assets/sintel1min720p.mkv")
        )
        await message.reply("✅ **Shield Active!**")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

@user_bot.on_message(filters.command(["ten_leave", "leave"], prefixes=["/", "!"]) & filters.group)
async def leave_vc(client, message):
    if not await is_authorized(message): return
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("👋 Leaving VC.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    call_py.start()
    user_bot.run()
