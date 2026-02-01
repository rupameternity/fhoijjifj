import os
import threading
import asyncio
import shutil
from flask import Flask

# --- THE PATCH (Error Fix) ---
import pyrogram.errors
class FakeError(Exception):
    pass
pyrogram.errors.GroupCallForbidden = FakeError
pyrogram.errors.GroupcallForbidden = FakeError
# ---------------------------------------

from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SESSION = os.environ.get("SESSION_STRING", "")
ALLOWED_GROUPS = [int(x.strip()) for x in os.environ.get("ALLOWED_GROUPS", "").split(",") if x.strip()]
SUDO_USERS = [int(x.strip()) for x in os.environ.get("SUDO_USERS", "").split(",") if x.strip()]

app = Flask(__name__)

@app.route('/')
def home():
    return "Poster Bot is Ultra Stable Now!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- BOT SETUP ---
user_bot = Client("poster_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

# Temporary storage for file paths to clean up later
active_files = {}

# 1. Security Check
@user_bot.on_message(filters.group)
async def security_check(client, message):
    if message.chat.id not in ALLOWED_GROUPS:
        try:
            await message.reply("❌ Unauthorized Group. Leaving...")
            await client.leave_chat(message.chat.id)
        except:
            pass
        return
    message.continue_propagation()

# 2. /go Command (Ultra Clean)
@user_bot.on_message(filters.command(["go"], prefixes=["/", "!"]) & filters.group)
async def start_stream(client, message):
    if message.from_user.id not in SUDO_USERS:
        return

    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("❗ Photo pe reply karke /go likho.")
        return

    chat_id = message.chat.id
    status = await message.reply("🛡️ **Starting Fresh Stream...**")

    try:
        # Purana session agar koi ho toh clear karo
        try:
            await call_py.leave_call(chat_id)
        except:
            pass

        # Photo download karo unique name ke sath
        file_path = await message.reply_to_message.download(file_name=f"stream_{chat_id}.jpg")
        active_files[chat_id] = file_path

        # Stream start (High Quality Settings)
        await call_py.play(
            chat_id, 
            MediaStream(
                file_path,
                video_flags=MediaStream.Flags.IGNORE_AUDIO
            )
        )
        
        await status.edit("✅ **Poster Attached Successfully.**")
        
    except Exception as e:
        await status.edit(f"❌ Error: {e}")

# 3. /leave Command (Full Reset)
@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def stop_stream(client, message):
    if message.from_user.id not in SUDO_USERS:
        return

    chat_id = message.chat.id
    try:
        # VC Leave karo
        await call_py.leave_call(chat_id)
        
        # Memory/File Clean karo
        if chat_id in active_files:
            file_to_del = active_files[chat_id]
            if os.path.exists(file_to_del):
                os.remove(file_to_del)
            del active_files[chat_id]

        await message.reply("👋 **Session Cleared & Poster Removed.**")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

if __name__ == "__main__":
    # Downloader folder clean up on start
    if os.path.exists("downloads"):
        shutil.rmtree("downloads")
    
    threading.Thread(target=run_flask).start()
    print("Bot Starting...")
    call_py.start()
    user_bot.run()
