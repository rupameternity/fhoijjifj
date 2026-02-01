import os
import sys
import threading
import asyncio
import signal
from flask import Flask
from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# --- 1. PATCH (Crash Fix) ---
import pyrogram.errors
class FakeError(Exception):
    pass
pyrogram.errors.GroupCallForbidden = FakeError
pyrogram.errors.GroupcallForbidden = FakeError
# ----------------------------

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
def home(): return "Bot is Running (Pipe Mode)"
def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), use_reloader=False)

# --- 4. BOT SETUP ---
user_bot = Client("poster_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

# Global Dictionary to manage FFmpeg processes
ffmpeg_processes = {}

# --- 5. LOGIC ---

@user_bot.on_message(filters.command(["reset", "restart"], prefixes=["/", "!"]) & filters.group)
async def restart_bot(client, message):
    if message.from_user.id not in SUDO_USERS: return
    await message.reply("🔄 **Rebooting...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

@user_bot.on_message(filters.command(["go"], prefixes=["/", "!"]) & filters.group)
async def start_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return

    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("❗ Photo pe reply karo.")
        return

    status = await message.reply("⚡ **Starting Live Stream...**")
    chat_id = message.chat.id
    pipe_path = f"pipe_{chat_id}"

    try:
        # --- CLEANUP OLD PROCESSES ---
        # Agar pehle se kuch chal raha hai to usko kill karo
        if chat_id in ffmpeg_processes:
            try:
                os.killpg(os.getpgid(ffmpeg_processes[chat_id].pid), signal.SIGTERM)
            except:
                pass
            del ffmpeg_processes[chat_id]
        
        # Purana call leave karo (Force Reset)
        try:
            await call_py.leave_call(chat_id)
            await asyncio.sleep(1)
        except:
            pass

        # Purana Pipe delete karo
        if os.path.exists(pipe_path):
            os.remove(pipe_path)
            
        # Naya Pipe banao (Linux Magic)
        os.mkfifo(pipe_path)

        # 1. Download Photo
        file_path = await message.reply_to_message.download()

        # 2. Start FFmpeg in BACKGROUND (Non-Blocking)
        # -re: Real-time speed (Atkega nahi)
        # -loop 1: Infinite Loop (4 sec baad band nahi hoga)
        # -f mpegts: Stream format (Pipe ke liye best)
        # -r 20: Smooth FPS
        
        cmd = (
            f'ffmpeg -hide_banner -loglevel error -re -loop 1 -i "{file_path}" '
            f'-c:v libx264 -preset ultrafast -tune stillimage -pix_fmt yuv420p '
            f'-vf "scale=854:480" -r 20 -g 60 -b:v 1000k -f mpegts "{pipe_path}"'
        )

        # Process start karo (Await mat karna communicate ke liye)
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            preexec_fn=os.setsid # Process Group banata hai kill karne ke liye
        )
        
        # Process ID save karlo taaki /leave pe band kar sakein
        ffmpeg_processes[chat_id] = process

        # 3. Stream from Pipe
        await call_py.play(
            chat_id, 
            MediaStream(pipe_path)
        )
        
        try:
            await call_py.mute_stream(chat_id)
        except:
            pass

        await status.edit("✅ **Live (Infinite Loop)!**")
        
        # Image delete kar sakte hain ab
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await status.edit(f"❌ Error: {e}")
        # Error aane pe pipe uda do
        if os.path.exists(pipe_path):
            os.remove(pipe_path)

@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def stop_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    chat_id = message.chat.id
    try:
        await call_py.leave_call(chat_id)
        await message.reply("👋 **Left.**")
        
        # --- IMPORTANT: KILL FFMPEG ---
        if chat_id in ffmpeg_processes:
            try:
                os.killpg(os.getpgid(ffmpeg_processes[chat_id].pid), signal.SIGTERM)
            except:
                pass
            del ffmpeg_processes[chat_id]
            
        # Pipe delete
        pipe_path = f"pipe_{chat_id}"
        if os.path.exists(pipe_path):
            os.remove(pipe_path)
            
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
