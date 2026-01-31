import os
import threading
import asyncio
from flask import Flask

# --- PATCH FOR PYROGRAM ERROR ---
import pyrogram.errors
class FakeError(Exception):
    pass
pyrogram.errors.GroupCallForbidden = FakeError
pyrogram.errors.GroupcallForbidden = FakeError
# -------------------------------

from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# --- CONFIG ---
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SESSION = os.environ.get("SESSION_STRING", "")

# IDs load karte waqt error handling
try:
    ALLOWED_GROUPS = [int(x.strip()) for x in os.environ.get("ALLOWED_GROUPS", "").split(",") if x.strip()]
    SUDO_USERS = [int(x.strip()) for x in os.environ.get("SUDO_USERS", "").split(",") if x.strip()]
except Exception as e:
    print(f"❌ Config Error: IDs sahi format mein nahi hain! {e}")
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

# --- DEBUG: Print every message to Logs ---
@user_bot.on_message(filters.group, group=-1)
async def logger(client, message):
    # Ye sirf Render logs mein dikhega taaki pata chale bot message padh raha hai
    print(f"📩 Msg received in {message.chat.id} from {message.from_user.id}: {message.text}")

# --- COMMANDS ---

@user_bot.on_message(filters.command(["go"], prefixes=["/", "!"]) & filters.group)
async def start_stream(client, message):
    print(f"➡️ Command /go detected from {message.from_user.id}")
    
    # 1. Check Permissions
    if message.from_user.id not in SUDO_USERS:
        print("⛔ User not in SUDO_USERS")
        return
    
    if message.chat.id not in ALLOWED_GROUPS:
        print("⛔ Group not in ALLOWED_GROUPS")
        await message.reply("❌ Unauthorized Group ID. Check Logs.")
        return

    # 2. Check Reply
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("❗ Photo pe reply karo.")
        return

    status = await message.reply("🔄 **Connecting to VC...**")

    try:
        file_path = await message.reply_to_message.download()
        print(f"✅ Photo downloaded: {file_path}")

        await call_py.play(
            message.chat.id, 
            MediaStream(
                file_path,
                video_flags=MediaStream.Flags.IGNORE_AUDIO
            )
        )
        await status.edit("✅ **Poster Streaming!**")
        print("✅ Stream Started")

    except Exception as e:
        print(f"❌ Error: {e}")
        await status.edit(f"❌ Error: {e}")

@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def stop_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("👋 **Poster Out.**")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# --- MAIN EXECUTION (FIXED ASYNC LOOP) ---
async def main():
    print("🚀 Starting Bot Services...")
    
    # Start Clients
    await user_bot.start()
    print("✅ Pyrogram Client Started")
    
    await call_py.start()
    print("✅ PyTgCalls Started")
    
    # Keep running
    await idle()
    
    # Stop cleanly
    await call_py.stop() # type: ignore
    await user_bot.stop()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
