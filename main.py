import os
import sys
import threading
import asyncio
from flask import Flask
from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# --- 1. CRASH FIX PATCH (Ye zaroori hai) ---
import pyrogram.errors
class FakeError(Exception):
    pass
pyrogram.errors.GroupCallForbidden = FakeError
pyrogram.errors.GroupcallForbidden = FakeError
# -------------------------------------------

# --- 2. CONFIG ---
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SESSION = os.environ.get("SESSION_STRING", "")

ALLOWED_GROUPS = []
SUDO_USERS = []
try:
    if os.environ.get("ALLOWED_GROUPS"):
        ALLOWED_GROUPS = [int(x.strip()) for x in os.environ.get("ALLOWED_GROUPS").split(",") if x.strip()]
    if os.environ.get("SUDO_USERS"):
        SUDO_USERS = [int(x.strip()) for x in os.environ.get("SUDO_USERS").split(",") if x.strip()]
except:
    pass

# --- 3. FLASK (Purana Wala Simple Server) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot Running"
def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- 4. BOT SETUP ---
user_bot = Client("poster_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

# --- 5. LOGIC ---

@user_bot.on_message(filters.command(["go"], prefixes=["/", "!"]) & filters.group)
async def start_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return

    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("❗ Photo pe reply karo.")
        return

    status = await message.reply("⚡ **Processing...**")
    chat_id = message.chat.id
    video_file = f"video_{chat_id}.mp4"

    try:
        # Purana session safai (Zaroori hai taaki bug na aaye)
        try:
            await call_py.leave_call(chat_id)
        except:
            pass

        if os.path.exists(video_file):
            os.remove(video_file)

        # 1. Download
        file_path = await message.reply_to_message.download()

        # 2. CONVERT (Ye hai main fix)
        # -r 1: Sirf 1 Frame/sec (Bohot fast banega)
        # -preset ultrafast: CPU use nahi karega
        # scale=854:480: Quality thodi kam ki hai taaki Render na atke
        
        process = await asyncio.create_subprocess_shell(
            f'ffmpeg -hide_banner -loglevel error -loop 1 -i "{file_path}" '
            f'-c:v libx264 -preset ultrafast -tune stillimage -pix_fmt yuv420p '
            f'-vf "scale=854:480" -r 1 -t 600 -y "{video_file}"',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Timeout error hata diya hai, bas hone ka wait karega
        await process.communicate()

        # 3. Stream
        await call_py.play(
            chat_id, 
            MediaStream(video_file)
        )
        
        # Audio Mute
        try:
            await call_py.mute_stream(chat_id)
        except:
            pass

        await status.edit("✅ **Streaming!**")
        
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await status.edit(f"❌ Error: {e}")
        # Error aaye to file delete kar do taaki space free rahe
        if os.path.exists(video_file):
            os.remove(video_file)

@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def stop_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("👋 **Left.**")
        
        # File delete
        video_file = f"video_{message.chat.id}.mp4"
        if os.path.exists(video_file):
            os.remove(video_file)
            
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

@user_bot.on_message(filters.command(["reset"], prefixes=["/", "!"]) & filters.group)
async def reset_bot(client, message):
    if message.from_user.id not in SUDO_USERS: return
    await message.reply("🔄 **Restarting...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

# --- 6. START ---
async def main():
    print("Bot Starting...")
    await user_bot.start()
    await call_py.start()
    print("Ready!")
    await idle()
    await call_py.stop()
    await user_bot.stop()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
