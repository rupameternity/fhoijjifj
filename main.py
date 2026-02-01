import os
import sys
import threading
import asyncio
from flask import Flask
from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# --- CRASH FIX PATCH ---
import pyrogram.errors
class FakeError(Exception):
    pass
pyrogram.errors.GroupCallForbidden = FakeError
pyrogram.errors.GroupcallForbidden = FakeError
# -----------------------

# --- CONFIG ---
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

# --- FLASK ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Online"
def run_flask():
    # use_reloader=False zaroori hai
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), use_reloader=False)

# --- BOT ---
user_bot = Client("poster_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

# --- CONVERTER (1 FPS - No Stuck) ---
async def convert_to_video_fast(input_path, output_path):
    cmd = (
        f'ffmpeg -hide_banner -loglevel error -loop 1 -i "{input_path}" '
        f'-c:v libx264 -preset ultrafast -tune stillimage -pix_fmt yuv420p '
        f'-vf "scale=1280:-2" -r 1 -t 600 -y "{output_path}"'
    )
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    # 20 second ka timeout taaki atke nahi
    try:
        await asyncio.wait_for(process.communicate(), timeout=20.0)
    except asyncio.TimeoutError:
        try:
            process.kill()
        except:
            pass
        raise Exception("Processing Timeout (Try again)")

# --- LOGIC ---

@user_bot.on_message(filters.command(["reset", "restart"], prefixes=["/", "!"]) & filters.group)
async def restart_bot(client, message):
    if message.from_user.id not in SUDO_USERS: return
    await message.reply("🔄 **Rebooting System...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

@user_bot.on_message(filters.command(["go"], prefixes=["/", "!"]) & filters.group)
async def start_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return

    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("❗ Photo pe reply karo.")
        return

    status = await message.reply("⚡ **Refreshing...**")
    chat_id = message.chat.id
    video_file = f"video_{chat_id}.mp4"

    try:
        # --- FIX FOR BUGS: Pehle purana session clear karo ---
        try:
            await call_py.leave_call(chat_id)
            await asyncio.sleep(1) # Telegram ko saans lene do
        except:
            pass
        
        # Purani files udao
        if os.path.exists(video_file):
            os.remove(video_file)

        # 1. Download
        file_path = await message.reply_to_message.download()

        # 2. Convert (Fast Mode)
        await convert_to_video_fast(file_path, video_file)

        # 3. Stream
        await call_py.play(
            chat_id, 
            MediaStream(video_file)
        )
        
        try:
            await call_py.mute_stream(chat_id)
        except:
            pass

        await status.edit("✅ **Live!**")
        
        # Image delete (Video rakhna padega)
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await status.edit(f"❌ Error: {e}")
        # Error aane pe bhi safai karo
        if os.path.exists(video_file):
            os.remove(video_file)

@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def stop_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("👋 **Left.**")
        
        video_file = f"video_{message.chat.id}.mp4"
        if os.path.exists(video_file):
            os.remove(video_file)
            
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# --- STARTUP ---
async def main():
    print("🚀 Bot Starting...")
    await user_bot.start()
    await call_py.start()
    print("✅ Ready!")
    await idle()
    await call_py.stop()
    await user_bot.stop()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
