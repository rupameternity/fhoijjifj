import os
import threading
import asyncio
from flask import Flask

# --- 1. CRASH FIX PATCH ---
import pyrogram.errors
class FakeError(Exception):
    pass
pyrogram.errors.GroupCallForbidden = FakeError
pyrogram.errors.GroupcallForbidden = FakeError
# --------------------------

from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# --- 2. CONFIG ---
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SESSION = os.environ.get("SESSION_STRING", "")

try:
    ALLOWED_GROUPS = [int(x.strip()) for x in os.environ.get("ALLOWED_GROUPS", "").split(",") if x.strip()]
    SUDO_USERS = [int(x.strip()) for x in os.environ.get("SUDO_USERS", "").split(",") if x.strip()]
except:
    ALLOWED_GROUPS = []
    SUDO_USERS = []

# --- 3. FLASK SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running!"

def run_flask():
    # use_reloader=False port conflict rokta hai
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False) 

# --- 4. BOT SETUP ---
user_bot = Client("poster_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

# --- 5. HELPER: Fast Video Converter ---
# Ye zaroori hai taaki 'Black Screen' na aaye aur 'Processing' pe na atke
async def convert_to_video_fast(input_path, output_path):
    cmd = (
        f'ffmpeg -hide_banner -loglevel error -loop 1 -i "{input_path}" '
        f'-c:v libx264 -preset ultrafast -tune stillimage -pix_fmt yuv420p '
        f'-vf "scale=1280:-2" -r 1 -t 3600 -y "{output_path}"'
    )
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()

# --- 6. LOGIC ---

@user_bot.on_message(filters.command(["go"], prefixes=["/", "!"]) & filters.group)
async def start_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    if message.chat.id not in ALLOWED_GROUPS:
        await message.reply("❌ Group Not Allowed")
        return

    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("❗ Photo pe reply karo.")
        return

    status = await message.reply("⚡ **Processing...**")

    try:
        # Purana call leave karo
        try:
            await call_py.leave_call(message.chat.id)
            await asyncio.sleep(1)
        except:
            pass

        # 1. Download
        file_path = await message.reply_to_message.download()
        video_file = f"video_{message.chat.id}.mp4"
        
        # 2. Convert (Fast Mode - 1 FPS)
        # Ye bohot jaldi ho jayega, atke ga nahi
        await convert_to_video_fast(file_path, video_file)

        # 3. Stream (ERROR FIX IS HERE)
        # Maine flags hata diye hain. Simple file path pass kar rahe hain.
        await call_py.play(
            message.chat.id,
            MediaStream(video_file)
        )
        
        # Audio ko alag se mute kar denge
        try:
            await call_py.mute_stream(message.chat.id)
        except:
            pass
        
        await status.edit("✅ **Poster Streaming!**")
        
        # Cleanup Image only (Video rehne do stream ke liye)
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        print(f"Error: {e}")
        await status.edit(f"❌ Error: {e}")


@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def stop_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("👋 **Poster Out.**")
        
        # Cleanup Video
        video_file = f"video_{message.chat.id}.mp4"
        if os.path.exists(video_file):
            os.remove(video_file)

    except Exception as e:
        await message.reply(f"❌ Error: {e}")


# --- 7. MAIN EXECUTION ---
async def main():
    print("🚀 Starting Bot...")
    await user_bot.start()
    await call_py.start()
    print("✅ Ready!")
    await idle()
    await call_py.stop()
    await user_bot.stop()

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
