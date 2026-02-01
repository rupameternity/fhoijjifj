import os
import threading
import asyncio
import signal
from flask import Flask

# --- PYROGRAM PATCH (Crash Fix) ---
import pyrogram.errors
class FakeError(Exception):
    pass
pyrogram.errors.GroupCallForbidden = FakeError
pyrogram.errors.GroupcallForbidden = FakeError
# ----------------------------------

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
def home(): return "Bot is Alive & Streaming!"
def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- GLOBAL VARIABLES ---
# FFmpeg process ko save karne ke liye taaki baad mein kill kar sakein
ffmpeg_processes = {}

# --- BOT SETUP ---
user_bot = Client("poster_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

@user_bot.on_message(filters.group, group=-1)
async def logger(client, message):
    pass 

# --- COMMANDS ---

@user_bot.on_message(filters.command(["go"], prefixes=["/", "!"]) & filters.group)
async def start_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    if message.chat.id not in ALLOWED_GROUPS:
        await message.reply("❌ Group Not Allowed")
        return

    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("reply a media")
        return

    status = await message.reply("🔄 **Setting up Live Stream...**")

    try:
        # 1. Purana stream cleanup karo agar hai toh
        if message.chat.id in ffmpeg_processes:
            try:
                ffmpeg_processes[message.chat.id].kill()
            except:
                pass
        
        # 2. Setup File Paths
        file_path = await message.reply_to_message.download()
        pipe_path = f"stream_{message.chat.id}.raw"

        # 3. Create Named Pipe (Agar pehle se nahi hai)
        if os.path.exists(pipe_path):
            os.remove(pipe_path)
        os.mkfifo(pipe_path)

        # 4. Start FFmpeg in BACKGROUND (Non-blocking)
        # -re: Read at native speed (Important for live stream)
        # -loop 1: Infinite loop input
        # -f mpegts: Pipe format
        print(f"Starting FFmpeg for {message.chat.id}")
        
        process = await asyncio.create_subprocess_shell(
            f'ffmpeg -re -loop 1 -i "{file_path}" -pix_fmt yuv420p -s 1280x720 -r 10 -b:v 500k -f mpegts "{pipe_path}"',
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            preexec_fn=os.setsid # Process group create karta hai easy kill ke liye
        )
        
        # Process ID save karo taaki /leave pe band kar sakein
        ffmpeg_processes[message.chat.id] = process

        # 5. Play the Pipe immediately
        await call_py.play(
            message.chat.id, 
            MediaStream(pipe_path) 
        )
        
        # Mute audio
        try:
            await call_py.mute_stream(message.chat.id)
        except:
            pass

        await status.edit("✅ **Live Poster Attached!**")
        
        # Original photo ki ab zaroorat nahi, pipe ban gaya
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        print(f"❌ Error: {e}")
        await status.edit(f"❌ Error: {e}")


@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def stop_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    
    try:
        # 1. Leave Call
        await call_py.leave_call(message.chat.id)
        await message.reply("👋 **Poster Out.**")
    except Exception as e:
        await message.reply(f"⚠️ **Force Stopped:** {e}")

    # 2. Kill FFmpeg Process (Important: CPU save karne ke liye)
    if message.chat.id in ffmpeg_processes:
        try:
            # Poore process group ko kill karo
            os.killpg(os.getpgid(ffmpeg_processes[message.chat.id].pid), signal.SIGTERM)
        except:
            pass
        del ffmpeg_processes[message.chat.id]

    # 3. Pipe file delete karo
    pipe_path = f"stream_{message.chat.id}.raw"
    if os.path.exists(pipe_path):
        os.remove(pipe_path)


# --- MAIN ---
async def main():
    print("🚀 Bot Starting...")
    await user_bot.start()
    await call_py.start()
    print("✅ System Online")
    await idle()
    await call_py.stop()
    await user_bot.stop()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
