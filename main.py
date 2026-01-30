import os
import threading
import asyncio
from flask import Flask
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING")

# Groups Config
ALLOWED_GROUPS = [int(x.strip()) for x in os.environ.get("ALLOWED_GROUPS", "").split(",") if x.strip()]
AUTHORIZED_USERS = [int(x.strip()) for x in os.environ.get("AUTHORIZED_USERS", "").split(",") if x.strip()]

app = Flask(__name__)
@app.route('/')
def home(): return "Glitch Fixer Active"
def run_flask(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- USERBOT SETUP ---
user_bot = Client("glitch_fixer", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

@user_bot.on_message(filters.command(["guard"], prefixes=["/", "!"]) & filters.group)
async def fix_glitch(client, message):
    if message.chat.id not in ALLOWED_GROUPS and message.from_user.id not in AUTHORIZED_USERS:
        return

    try:
        msg = await message.reply("🛡️ **Stabilizing Packets...**")
        
        # TRICK: Hum ek 'Live Stream' play kar rahe hain.
        # Live stream ko Telegram High Priority deta hai aur packet drop nahi karta.
        # Isse Glitch hona band ho jata hai.
        await call_py.play(
            message.chat.id, 
            MediaStream(
                "http://docs.evostream.com/sample_content/assets/sintel1min720p.mkv"
            )
        )
        # Khud ko mute kar lega taaki shor na ho
        await call_py.mute_stream(message.chat.id)
        
        await msg.edit("✅ **VC Secured on High-Speed Server.**\nAb glitch nahi hoga. Mujhe kick mat karna.")
    except Exception as e:
        await msg.edit(f"❌ Error: {e}")

@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def leave_vc(client, message):
    if message.from_user.id not in AUTHORIZED_USERS: return
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("👋 Guard Removed.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    call_py.start()
    user_bot.run()
