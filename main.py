import os
import sys
import threading
import asyncio
import gc  # Garbage Collector (RAM Safai ke liye)
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
def home(): return "Bot is Alive (Low RAM Mode)"
def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), use_reloader=False)

# --- 4. BOT SETUP ---
user_bot = Client("poster_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

# --- 5. LOGIC ---

@user_bot.on_message(filters.command(["reset", "restart"], prefixes=["/", "!"]) & filters.group)
async def restart_bot(client, message):
    if message.from_user.id not in SUDO_USERS: return
    await message.reply("🔄 **Rebooting & Clearing RAM...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

@user_bot.on_message(filters.command(["go"], prefixes=["/", "!"]) & filters.group)
async def start_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return

    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("❗ Photo pe reply karo.")
        return

    status = await message.reply("⚡ **Optimizing & Joining...**")
    chat_id = message.chat.id

    try:
        # STEP 1: FORCE RESET (Processing Stuck Fix)
        try:
            await call_py.leave_call(chat_id)
            await asyncio.sleep(1.5)
        except:
            pass
            
        # STEP 2: RAM CLEANUP
        gc.collect() # Python ki memory saaf karo

        # STEP 3: DOWNLOAD
        original_path = await message.reply_to_message.download()
        compressed_path = f"small_{chat_id}.jpg"

        # --- STEP 4: MAGIC RESIZE (RAM Saver) ---
        # Image ko 640px width pe resize karo (Bohot halka ho jayega)
        # Ye command 4MB ki photo ko 50KB bana degi.
        os.system(f'ffmpeg -hide_banner -loglevel error -i "{original_path}" -vf scale=640:-1 -q:v 20 "{compressed_path}" -y')
        
        # Original bhari file delete karo
        if os.path.exists(original_path):
            os.remove(original_path)

        # STEP 5: STREAM LOW QUALITY IMAGE
        await call_py.play(
            chat_id, 
            MediaStream(compressed_path)
        )
        
        try:
            await call_py.mute_stream(chat_id)
        except:
            pass

        await status.edit("✅ **Stream Live!** (Low RAM)")
        
        # Compressed file bhi uda do (RAM mein load ho chuki hai)
        if os.path.exists(compressed_path):
            os.remove(compressed_path)
            
        # Final RAM Sweep
        gc.collect()

    except Exception as e:
        await status.edit(f"❌ Error: {e}")

@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def stop_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("👋 **Left.**")
        gc.collect() # RAM Safai
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
