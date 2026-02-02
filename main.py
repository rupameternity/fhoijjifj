import os
import sys
import threading
import asyncio
import gc
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
def home(): return "Bot is Alive (Audio Fix)"
def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), use_reloader=False)

# --- 4. BOT SETUP ---
user_bot = Client("poster_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

# --- 5. LOGIC ---

@user_bot.on_message(filters.command(["reset", "restart"], prefixes=["/", "!"]) & filters.group)
async def restart_bot(client, message):
    if message.from_user.id not in SUDO_USERS: return
    await message.reply("🔄 **Rebooting System...**")
    gc.collect()
    os.execl(sys.executable, sys.executable, *sys.argv)

@user_bot.on_message(filters.command(["go"], prefixes=["/", "!"]) & filters.group)
async def start_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return

    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("no photo found")
        return

    status = await message.reply("loading
    ")
    chat_id = message.chat.id

    try:
        # STEP 1: RESET CONNECTION
        try:
            await call_py.leave_call(chat_id)
            await asyncio.sleep(1.5)
        except:
            pass
        
        gc.collect()

        # STEP 2: DOWNLOAD
        original_path = await message.reply_to_message.download()
        video_file = f"stream_{chat_id}.mp4"

        # --- STEP 3: THE FIX (Add Silent Audio) ---
        # -f lavfi -i anullsrc: Ye ek 'Empty Audio' input create karta hai.
        # -c:a aac: Audio ko AAC format mein convert karta hai (Telegram supported).
        # -shortest: Audio ko video ki length (30 mins) tak hi rakhta hai.
        
        cmd = (
            f'ffmpeg -hide_banner -loglevel error -loop 1 -i "{original_path}" '
            f'-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 '
            f'-c:v libx264 -preset ultrafast -tune stillimage -pix_fmt yuv420p '
            f'-c:a aac -shortest '
            f'-vf "scale=1280:-2" -r 1 -t 1800 -y "{video_file}"'
        )

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # 30-40 sec timeout for 30 min file (Render speed check)
        try:
            await asyncio.wait_for(process.communicate(), timeout=40.0)
        except asyncio.TimeoutError:
            process.kill()

        if os.path.exists(original_path):
            os.remove(original_path)

        # STEP 4: STREAM
        # Ab ye file normal video hai (Audio+Video), to error nahi aayega.
        await call_py.play(
            chat_id, 
            MediaStream(video_file)
        )
        
        # Ab hum 'mute' nahi karenge kyunki audio already silent hai
        
        await status.edit("live")
        gc.collect()

    except Exception as e:
        await status.edit(f"❌ Error: {e}")
        if os.path.exists(video_file):
            os.remove(video_file)

@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def stop_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("👋 **Left.**")
        
        if os.path.exists(f"stream_{message.chat.id}.mp4"):
            os.remove(f"stream_{message.chat.id}.mp4")
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
