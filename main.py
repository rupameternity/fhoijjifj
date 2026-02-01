import os
import threading
import asyncio
import shutil
from flask import Flask
import pyrogram.errors

# --- THE PATCH ---
class FakeError(Exception):
    pass
pyrogram.errors.GroupCallForbidden = FakeError
pyrogram.errors.GroupcallForbidden = FakeError
# -----------------

from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from pytgcalls.types import Flags # <--- Flags yahan se import hoga

# --- CONFIG ---
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SESSION = os.environ.get("SESSION_STRING", "")
ALLOWED_GROUPS = [int(x.strip()) for x in os.environ.get("ALLOWED_GROUPS", "").split(",") if x.strip()]
SUDO_USERS = [int(x.strip()) for x in os.environ.get("SUDO_USERS", "").split(",") if x.strip()]

app = Flask(__name__)
active_files = {}

@app.route('/')
def home():
    return "Bot is running perfectly!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

user_bot = Client("poster_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

@user_bot.on_message(filters.command(["go"], prefixes=["/", "!"]) & filters.group)
async def start_stream(client, message):
    if message.from_user.id not in SUDO_USERS or message.chat.id not in ALLOWED_GROUPS:
        return
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("❗ Photo pe reply karke /go likho.")
        return

    chat_id = message.chat.id
    status = await message.reply("🛡️ **Starting...**")
    try:
        try: await call_py.leave_call(chat_id)
        except: pass
        
        file_path = await message.reply_to_message.download(file_name=f"stream_{chat_id}.jpg")
        active_files[chat_id] = file_path

        # FIX: Naye version ke liye Flags.IGNORE_AUDIO use kar rahe hain
        await call_py.play(
            chat_id, 
            MediaStream(
                file_path, 
                video_flags=Flags.IGNORE_AUDIO # <--- Ye line ab sahi se kaam karegi
            )
        )
        await status.edit("✅ **Poster Attached.**")
    except Exception as e:
        await status.edit(f"❌ Error: {e}")

@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def stop_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    chat_id = message.chat.id
    try:
        await call_py.leave_call(chat_id)
        if chat_id in active_files and os.path.exists(active_files[chat_id]):
            os.remove(active_files[chat_id])
            del active_files[chat_id]
        await message.reply("👋 **Session Cleared.**")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

async def main():
    if os.path.exists("downloads"):
        shutil.rmtree("downloads")
    threading.Thread(target=run_flask, daemon=True).start()
    await user_bot.start()
    await call_py.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
