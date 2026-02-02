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
    print("⚠️ Config Error: IDs check kar lena.")
    ALLOWED_GROUPS = []
    SUDO_USERS = []

# --- 3. FLASK SERVER ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Alive!"
def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), use_reloader=False)

# --- 4. BOT SETUP ---
user_bot = Client("poster_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

# --- 5. LOGIC ---

# Auto-Leave Unauthorized Groups
@user_bot.on_message(filters.group)
async def security_check(client, message):
    if message.chat.id not in ALLOWED_GROUPS:
        return 
    message.continue_propagation()

# --- RESET COMMAND ---
@user_bot.on_message(filters.command(["reset", "restart"], prefixes=["/", "!"]) & filters.group)
async def restart_bot(client, message):
    if message.from_user.id not in SUDO_USERS: return
    
    await message.reply("🔄 **Restarting System...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

@user_bot.on_message(filters.command(["go"], prefixes=["/", "!"]) & filters.group)
async def start_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return

    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("❗ Photo pe reply karke /go likho.")
        return

    status = await message.reply("⚡ **Refreshing & Connecting...**")
    chat_id = message.chat.id

    try:
        # --- FIX ADDED HERE (Connection Reset) ---
        # Ye naya code hai: Join karne se pehle purana connection tod do.
        # Isse "Processing" wala stuck issue solve ho jayega.
        try:
            await call_py.leave_call(chat_id)
            await asyncio.sleep(2) # 2 second ruko taaki Telegram server update ho jaye
        except:
            pass
        # -----------------------------------------

        # 1. Download
        file_path = await message.reply_to_message.download()

        # 2. Join & Stream
        await call_py.play(
            chat_id, 
            MediaStream(file_path)
        )
        
        # 3. Mute
        try:
            await call_py.mute_stream(chat_id)
        except:
            pass

        await status.edit("✅ **Poster Streaming!**")
        
        # Cleanup (Optional: Agar disk full hone ka dar ho to ise uncomment kar dena)
        # if os.path.exists(file_path):
        #     os.remove(file_path)

    except Exception as e:
        await status.edit(f"❌ Error: {e}")

@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def stop_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("👋 **Poster Out.**")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# --- 6. STARTUP ---
async def main():
    print("🚀 Bot Starting...")
    await user_bot.start()
    await call_py.start()
    print("✅ Bot Ready! /go use karo.")
    await idle()
    await call_py.stop()
    await user_bot.stop()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
