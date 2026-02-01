import os
import sys
import threading
import asyncio
from flask import Flask

# --- PATCH (Crash Fix) ---
import pyrogram.errors
class FakeError(Exception):
    pass
pyrogram.errors.GroupCallForbidden = FakeError
pyrogram.errors.GroupcallForbidden = FakeError
# -------------------------

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

# --- FLASK SERVER ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Alive"
def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- BOT SETUP ---
user_bot = Client("poster_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

@user_bot.on_message(filters.group, group=-1)
async def logger(client, message):
    pass

# --- HELPER: Fast Video Converter ---
async def convert_to_video_fast(input_path, output_path):
    # Magic Settings for Low-End Servers (Render):
    # -r 1: Sirf 1 Frame per Second (Rendering super fast hogi)
    # -t 1800: 30 Minute ki video banegi (Par size bohot kam hoga)
    # -preset ultrafast: CPU pe load nahi dalega
    
    cmd = (
        f'ffmpeg -hide_banner -loglevel error -loop 1 -i "{input_path}" '
        f'-c:v libx264 -preset ultrafast -tune stillimage -pix_fmt yuv420p '
        f'-vf "scale=1280:-2" -r 1 -t 1800 -y "{output_path}"'
    )
    
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()

# --- COMMANDS ---

@user_bot.on_message(filters.command(["reset", "restart"], prefixes=["/", "!"]) & filters.group)
async def restart_bot(client, message):
    if message.from_user.id not in SUDO_USERS: return
    
    await message.reply("🔄 **Force Restarting Bot...** (Wait 10s)")
    # Ye command poore bot ko band karke firse chalu kar degi
    os.execl(sys.executable, sys.executable, *sys.argv)

@user_bot.on_message(filters.command(["go"], prefixes=["/", "!"]) & filters.group)
async def start_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    if message.chat.id not in ALLOWED_GROUPS:
        await message.reply("❌ Group Not Allowed")
        return

    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("❗ Photo pe reply karo.")
        return

    status = await message.reply("⚡ **Processing (Fast Mode)...**")

    try:
        # 1. Purana leave karo agar hai
        try:
            await call_py.leave_call(message.chat.id)
        except:
            pass

        # 2. Download
        file_path = await message.reply_to_message.download()
        video_file = f"video_{message.chat.id}.mp4"

        # 3. Fast Convert
        await convert_to_video_fast(file_path, video_file)

        # 4. Stream
        await call_py.play(
            message.chat.id, 
            MediaStream(video_file) 
        )
        
        # Audio Mute
        try:
            await call_py.mute_stream(message.chat.id)
        except:
            pass
            
        await status.edit("✅ **Poster Streaming!** (30 Mins)")
        
        # Cleanup Image (Video rakhni padegi stream ke liye)
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await status.edit(f"❌ Error: {e}")

@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def stop_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("👋 **Poster Out.**")
        
        # Video file delete kar do space bachane ke liye
        video_file = f"video_{message.chat.id}.mp4"
        if os.path.exists(video_file):
            os.remove(video_file)
            
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
