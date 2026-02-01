import os
import sys
import threading
import asyncio
import signal
from flask import Flask
from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# --- 1. CRASH FIX PATCH ---
import pyrogram.errors
class FakeError(Exception):
    pass
pyrogram.errors.GroupCallForbidden = FakeError
pyrogram.errors.GroupcallForbidden = FakeError
# --------------------------

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

# --- 3. FLASK SERVER ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Ready"
def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), use_reloader=False)

# --- 4. BOT SETUP ---
user_bot = Client("poster_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

# --- 5. SYSTEM CLEANER (Ye hai Jadu) ---
# Ye function har baar purana kachra saaf karega
async def nuclear_cleanup(chat_id):
    print(f"⚠️ Performing Nuclear Cleanup for {chat_id}...")
    
    # 1. Force Kill FFmpeg (System level pe process maarega)
    try:
        os.system("pkill -9 ffmpeg")
    except:
        pass

    # 2. Leave Call forcefully
    try:
        await call_py.leave_call(chat_id)
        await asyncio.sleep(1.5) # Thoda time do Telegram ko update hone ke liye
    except:
        pass
    
    # 3. Delete ALL .mp4 files in directory (Disk space clear)
    try:
        for file in os.listdir():
            if file.endswith(".mp4"):
                os.remove(file)
    except:
        pass

# --- 6. FAST CONVERTER (360p = No Lag) ---
async def convert_to_video_fast(input_path, output_path):
    # scale=640:-2 (360p) taaki Render Free Tier pe load na aaye
    # -t 3600 (1 Ghanta chalega)
    cmd = (
        f'ffmpeg -hide_banner -loglevel error -loop 1 -i "{input_path}" '
        f'-c:v libx264 -preset ultrafast -tune stillimage -pix_fmt yuv420p '
        f'-vf "scale=640:-2" -r 1 -t 3600 -y "{output_path}"'
    )
    
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # Timeout increased to 90s just in case, but usually takes 3s
    try:
        await asyncio.wait_for(process.communicate(), timeout=90.0)
    except asyncio.TimeoutError:
        try:
            process.kill()
        except:
            pass
        # Agar timeout ho jaye, to script restart kar do (Last Resort)
        os.execl(sys.executable, sys.executable, *sys.argv)

# --- 7. LOGIC ---

@user_bot.on_message(filters.command(["go"], prefixes=["/", "!"]) & filters.group)
async def start_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return

    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("❗ Photo pe reply karo.")
        return

    # User ko batao hum safai kar rahe hain
    status = await message.reply("🧹 **Cleaning & Restarting Stream...**")
    chat_id = message.chat.id
    
    try:
        # --- STEP 1: SAB KUCH DELETE/KILL KARO ---
        await nuclear_cleanup(chat_id)

        # --- STEP 2: FRESH START ---
        file_path = await message.reply_to_message.download()
        video_file = f"video_{chat_id}.mp4"

        # Convert
        await convert_to_video_fast(file_path, video_file)

        # Stream
        await call_py.play(
            chat_id, 
            MediaStream(video_file)
        )
        
        try:
            await call_py.mute_stream(chat_id)
        except:
            pass

        await status.edit("✅ **Live (Fresh Session)!**")
        
        # Image delete
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await status.edit(f"❌ Error: {e}")
        # Error aane pe bhi safai
        await nuclear_cleanup(chat_id)

@user_bot.on_message(filters.command(["leave", "stop"], prefixes=["/", "!"]) & filters.group)
async def stop_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    try:
        await nuclear_cleanup(message.chat.id)
        await message.reply("👋 **Session Cleared.**")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# --- 8. STARTUP ---
async def main():
    print("🚀 Bot Starting...")
    # Startup pe bhi safai
    os.system("pkill -9 ffmpeg")
    
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
