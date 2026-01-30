import os
import threading
from flask import Flask
from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# --- FAKE ERROR PATCH (Isse mat hatana) ---
import pyrogram.errors
class FakeError(Exception): pass
pyrogram.errors.GroupCallForbidden = FakeError
pyrogram.errors.GroupcallForbidden = FakeError
# ------------------------------------------

# --- CONFIG ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING")

ALLOWED_GROUPS = [int(x.strip()) for x in os.environ.get("ALLOWED_GROUPS", "").split(",") if x.strip()]
AUTHORIZED_USERS = [int(x.strip()) for x in os.environ.get("AUTHORIZED_USERS", "").split(",") if x.strip()]

app = Flask(__name__)
@app.route('/')
def home(): return "Glitch Guard Active"
def run_flask(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- BOT SETUP ---
user_bot = Client("glitch_guard", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

@user_bot.on_message(filters.command(["guard"], prefixes=["/", "!"]) & filters.group)
async def start_guard(client, message):
    if message.chat.id not in ALLOWED_GROUPS and message.from_user.id not in AUTHORIZED_USERS: return
    try:
        msg = await message.reply("🛡️ **Anchoring VC...**")
        await call_py.play(
            message.chat.id, 
            MediaStream("http://docs.evostream.com/sample_content/assets/sintel1min720p.mkv")
        )
        await call_py.mute_stream(message.chat.id)
        await msg.edit("✅ **Secured.**")
    except Exception as e:
        await msg.edit(f"❌ Error: {e}")

@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def stop_guard(client, message):
    if message.from_user.id not in AUTHORIZED_USERS: return
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("👋 Guard Removed.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# --- STARTUP FIX (Ye error theek karega) ---
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    
    # Pehle Client start karenge, fir PyTgCalls, fir Idle
    # Isse "Already Connected" wala error nahi aayega
    user_bot.start()
    call_py.start()
    print("--- BOT STARTED ---")
    idle()
    user_bot.stop()
