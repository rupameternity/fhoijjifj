import os
import threading
import asyncio
from flask import Flask

# --- PATCH (Rehne do) ---
import pyrogram.errors
class FakeError(Exception):
    pass
pyrogram.errors.GroupCallForbidden = FakeError
pyrogram.errors.GroupcallForbidden = FakeError
# ------------------------

from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# --- CONFIG ---
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SESSION = os.environ.get("SESSION_STRING", "")

try:
    ALLOWED_GROUPS = [int(x.strip()) for x in os.environ.get("ALLOWED_GROUPS", "").split(",") if x.strip()]
    SUDO_USERS = [int(x.strip()) for x in os.environ.get("SUDO_USERS", "").split(",") if x.strip()]
except:
    ALLOWED_GROUPS = []
    SUDO_USERS = []

# --- FLASK ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Alive"
def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- HELPER: Image to Video Converter ---
async def convert_to_video(input_path, output_path):
    # FFmpeg command:
    # -loop 1: Image ko repeat karo
    # -t 3600: 1 ghante tak (infinite feel)
    # -pix_fmt yuv420p: Ye line sabse IMPORTANT hai (Telegram compatibility)
    # -vf scale: Size ko even number banata hai taaki crash na ho
    
    process = await asyncio.create_subprocess_shell(
        f'ffmpeg -hide_banner -loglevel error -loop 1 -i "{input_path}" -c:v libx264 -preset ultrafast -tune stillimage -pix_fmt yuv420p -vf "scale=1280:-2" -r 5 -t 3600 -y "{output_path}"',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()

# --- BOT SETUP ---
user_bot = Client("poster_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

@user_bot.on_message(filters.group, group=-1)
async def logger(client, message):
    pass # Logs clean rakhne ke liye hata diya

# --- COMMANDS ---

@user_bot.on_message(filters.command(["go"], prefixes=["/", "!"]) & filters.group)
async def start_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    if message.chat.id not in ALLOWED_GROUPS:
        await message.reply("❌ Group Not Allowed")
        return

    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("❗ Photo pe reply karo.")
        return

    status = await message.reply("🔄 **Generating Video Stream...**")

    try:
        # 1. Download Photo
        file_path = await message.reply_to_message.download()
        video_file = f"{file_path}.mp4"

        # 2. Convert to Video (Ye black screen fix karega)
        await convert_to_video(file_path, video_file)

        # 3. Stream the Video
        await call_py.play(
            message.chat.id, 
            MediaStream(video_file) 
        )
        
        # 4. Audio Mute
        try:
            await call_py.mute_stream(message.chat.id)
        except:
            pass
            
        await status.edit("✅ **Poster Streaming!**")
        
        # Cleanup: Original photo delete kar do, video rehne do stream ke liye
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        print(f"❌ Error: {e}")
        await status.edit(f"❌ Error: {e}")

@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def stop_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("👋 **Poster Out.**")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# --- MAIN ---
async def main():
    print("🚀 Bot Starting...")
    await user_bot.start()
    await call_py.start()
    await idle()
    await call_py.stop()
    await user_bot.stop()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
