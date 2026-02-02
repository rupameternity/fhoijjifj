import os
import sys
import threading
import asyncio
import gc
import time
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

try:
    ALLOWED_GROUPS = [int(x.strip()) for x in os.environ.get("ALLOWED_GROUPS", "").split(",") if x.strip()]
    SUDO_USERS = [int(x.strip()) for x in os.environ.get("SUDO_USERS", "").split(",") if x.strip()]
except:
    ALLOWED_GROUPS = []
    SUDO_USERS = []

# --- 3. FLASK SERVER ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Alive (Auto-Loop Mode)"
def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), use_reloader=False)

# --- 4. BOT SETUP ---
user_bot = Client("poster_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

# Global flag to control the loop
stream_active = {}

# --- 5. LOGIC ---

@user_bot.on_message(filters.command(["reset", "restart"], prefixes=["/", "!"]) & filters.group)
async def restart_bot(client, message):
    if message.from_user.id not in SUDO_USERS: return
    await message.reply("🔄 **Rebooting...**")
    gc.collect()
    os.execl(sys.executable, sys.executable, *sys.argv)

@user_bot.on_message(filters.command(["go"], prefixes=["/", "!"]) & filters.group)
async def start_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return

    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("❗ Photo pe reply karo.")
        return

    chat_id = message.chat.id
    status = await message.reply("⚡ **Generating (5 Min Loop)...**")

    try:
        # STEP 1: RESET
        stream_active[chat_id] = False # Stop old loops
        try:
            await call_py.leave_call(chat_id)
            await asyncio.sleep(1)
        except:
            pass
        gc.collect()

        # STEP 2: DOWNLOAD
        original_path = await message.reply_to_message.download()
        video_file = f"stream_{chat_id}.mp4"

        # --- STEP 3: CREATE 5 MINUTE VIDEO ---
        # -t 300: 5 Minutes only (Turant ban jayega)
        # -r 1: 1 FPS (CPU bachane ke liye)
        # scale=640:-2: 360p (RAM bachane ke liye)
        # anullsrc: Fake Audio (Error fix)
        
        cmd = (
            f'ffmpeg -hide_banner -loglevel error -loop 1 -i "{original_path}" '
            f'-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 '
            f'-map 0:v -map 1:a '
            f'-c:v libx264 -preset ultrafast -tune stillimage -pix_fmt yuv420p '
            f'-c:a aac -b:a 32k '
            f'-vf "scale=640:-2" -r 1 -t 300 -y "{video_file}"'
        )

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # 5 min ki video 10 sec ke andar ban jani chahiye
        try:
            await asyncio.wait_for(process.communicate(), timeout=30.0)
        except asyncio.TimeoutError:
            process.kill()
            await status.edit("❌ **Timeout:** Server slow hai.")
            return

        if os.path.exists(original_path):
            os.remove(original_path)

        # Check if file is valid
        if os.path.getsize(video_file) < 1000:
            await status.edit("❌ **Error:** File empty bani.")
            return

        # --- STEP 4: START STREAM WITH AUTO-LOOP ---
        stream_active[chat_id] = True
        await status.edit("✅ **Live! (Auto-Loop On)**")
        
        # Ye background mein chalega
        asyncio.create_task(run_loop(chat_id, video_file))

    except Exception as e:
        await status.edit(f"❌ Error: {e}")
        if os.path.exists(video_file):
            os.remove(video_file)

async def run_loop(chat_id, video_file):
    # Ye function har 5 min baad video ko firse play karega
    while stream_active.get(chat_id):
        try:
            await call_py.play(chat_id, MediaStream(video_file))
            # 5 Minute (300 sec) wait karo, fir loop hoga
            # Hum thoda kam wait karenge taaki gap na aaye
            await asyncio.sleep(295) 
        except Exception as e:
            print(f"Loop Error: {e}")
            break

@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def stop_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    chat_id = message.chat.id
    stream_active[chat_id] = False # Loop stop karo
    
    try:
        await call_py.leave_call(chat_id)
        await message.reply("👋 **Left.**")
        
        if os.path.exists(f"stream_{chat_id}.mp4"):
            os.remove(f"stream_{chat_id}.mp4")
        gc.collect()
        
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# --- 6. STARTUP ---
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
