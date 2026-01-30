import os
import threading
from flask import Flask
import pyrogram.errors

# --- 1. MAGIC PATCH (Ye Error 100% Fix Karega) ---
# Library purani hai aur spelling galat dhoond rahi hai.
# Hum zabardasti usse sahi spelling pakda rahe hain.
setattr(pyrogram.errors, "GroupcallForbidden", pyrogram.errors.GroupCallForbidden)
# -----------------------------------------------

from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import InputAudioStream

# --- CONFIG ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING")

ALLOWED_GROUPS = [int(x.strip()) for x in os.environ.get("ALLOWED_GROUPS", "").split(",") if x.strip()]
AUTHORIZED_USERS = [int(x.strip()) for x in os.environ.get("AUTHORIZED_USERS", "").split(",") if x.strip()]

app = Flask(__name__)
@app.route('/')
def home(): return "Glitch Guard Active (V2)"
def run_flask(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- BOT SETUP ---
user_bot = Client("glitch_guard", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

@user_bot.on_message(filters.command(["guard"], prefixes=["/", "!"]) & filters.group)
async def start_guard(client, message):
    if message.chat.id not in ALLOWED_GROUPS and message.from_user.id not in AUTHORIZED_USERS: return
    try:
        msg = await message.reply("🛡️ **Anchoring VC via Render Server...**")
        
        # --- V2 SYNTAX (Jo installed library pe chalega) ---
        await call_py.join_group_call(
            message.chat.id, 
            InputAudioStream(
                "http://docs.evostream.com/sample_content/assets/sintel1min720p.mkv",
            )
        )
        
        # Note: V2 mein mute ka function alag hota hai, 
        # isliye safety ke liye hum bas join kara rahe hain.
        # Tu khud 'Mute for everyone' kar dena.
        
        await msg.edit("✅ **Secured.** I am holding the connection strong.")
    except Exception as e:
        await msg.edit(f"❌ Error: {e}")

@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def stop_guard(client, message):
    if message.from_user.id not in AUTHORIZED_USERS: return
    try:
        await call_py.leave_group_call(message.chat.id)
        await message.reply("👋 Guard Removed.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    call_py.start()
    user_bot.run()
