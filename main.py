import os
import sys
import threading
import asyncio
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
def home(): return "Bot is Active"
def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), use_reloader=False)

# --- 4. BOT SETUP ---
user_bot = Client("poster_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

# --- 5. HELPER: ROBUST CONVERTER ---
async def convert_to_video_fast(input_path, output_path):
    # -r 1: 1 FPS (Low CPU)
    # -pix_fmt yuv420p: (No Black Screen)
    # timeout: Agar 20 sec mein nahi hua to error dega (Atkega nahi)
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
    # Wait with timeout
    try:
        await asyncio.wait_for(process.communicate(), timeout=20.0)
    except asyncio.TimeoutError:
        process.kill()
        raise Exception("FFmpeg Timeout: Server Slow hai, dubara try karo.")

# --- 6. LOGIC ---

@user_bot.on_message(filters.command(["reset", "restart"], prefixes=["/", "!"]) & filters.group)
async def restart_bot(client, message):
    if message.from_user.id not in SUDO_USERS: return
    await message.reply("🔄 **Force Rebooting System...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

@user_bot.on_message(filters.command(["go"], prefixes=["/", "!"]) & filters.group)
async def start_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    
    # 1. Check Reply
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("❗ Photo pe reply karo.")
        return

    status = await message.reply("⚡ **Refreshing & Joining...**")
    chat_id = message.chat.id
    video_file = f"video_{chat_id}.mp4"

    try:
        # --- CRITICAL FIX: FORCE LEAVE FIRST ---
        # Naya VC join karne se pehle purana session clear karna zaroori hai
        # Chahe wo join ho ya na ho, try leaving.
        try:
            await call_py.leave_call(chat_id)
            await asyncio.sleep(2) # Telegram ko update hone do
        except:
            pass # Agar already left hai to koi baat nahi
        
        # Clean Old Files
        if os.path.exists(video_file):
            os.remove(video_file)

        # 2. Download
        file_path = await message.reply_to_message.download()

        # 3. Convert
        await convert_to_video_fast(file_path, video_file)

        # 4. Stream
        await call_py.play(
            chat_id, 
            MediaStream(video_file)
        )
        
        # Mute (Optional)
        try:
            await call_py.mute_stream(chat_id)
        except:
            pass

        await status.edit("✅ **Poster Live!**")
        
        # Clean Image
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await status.edit(f"❌ Error: {e}")
        # Agar error aaye, to safai kar do taaki agli baar chal sake
        if os.path.exists(video_file):
            os.remove(video_file)

@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def stop_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("👋 **Left.**")
        
        # Clean Video
        video_file = f"video_{message.chat.id}.mp4"
        if os.path.exists(video_file):
            os.remove(video_file)
            
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# --- 7. STARTUP ---
async def main():
    print("🚀 Bot Starting...")
    await user_bot.start()
    await call_py.start()
    print("✅ Bot Ready!")
    await idle()
    await call_py.stop()
    await user_bot.stop()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
