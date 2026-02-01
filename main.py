import os
import sys  # Restart karne ke liye ye zaroori hai
import threading
import asyncio
from flask import Flask

# --- THE PATCH (Jo error fix karega) ---
import pyrogram.errors
class FakeError(Exception):
    pass

pyrogram.errors.GroupCallForbidden = FakeError
pyrogram.errors.GroupcallForbidden = FakeError
# ---------------------------------------

from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SESSION = os.environ.get("SESSION_STRING", "")

ALLOWED_GROUPS = [int(x.strip()) for x in os.environ.get("ALLOWED_GROUPS", "").split(",") if x.strip()]
SUDO_USERS = [int(x.strip()) for x in os.environ.get("SUDO_USERS", "").split(",") if x.strip()]

# --- FLASK SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Poster Bot is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- BOT SETUP ---
user_bot = Client("poster_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

# --- LOGIC SECTIONS ---

# 1. Security Check (Auto Leave)
@user_bot.on_message(filters.group)
async def security_check(client, message):
    if message.chat.id not in ALLOWED_GROUPS:
        try:
            await message.reply("❌ Unauthorized Group. Leaving...")
            await client.leave_chat(message.chat.id)
        except:
            pass
        return
    message.continue_propagation()

# --- NEW: RESET COMMAND (Agar bot atak jaye to ye use karna) ---
@user_bot.on_message(filters.command(["reset", "restart"], prefixes=["/", "!"]) & filters.group)
async def restart_bot(client, message):
    if message.from_user.id not in SUDO_USERS:
        return
    
    await message.reply("🔄 **Bot Restart ho raha hai...** (Wait 5 sec)")
    # Ye command bot ko band karke wapas chalu kar degi
    os.execl(sys.executable, sys.executable, *sys.argv)


# 2. /go Command
@user_bot.on_message(filters.command(["go"], prefixes=["/", "!"]) & filters.group)
async def start_stream(client, message):
    if message.from_user.id not in SUDO_USERS:
        return

    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("❗ Photo pe reply karke /go likho.")
        return

    status = await message.reply("🛡️ **Processing Image...**")

    try:
        # Photo download karo
        file_path = await message.reply_to_message.download()

        # Stream start karo
        # NOTE: Maine yahan se 'IGNORE_AUDIO' hata diya kyunki wo crash kar raha tha.
        # Ab ye direct join karega.
        await call_py.play(
            message.chat.id, 
            MediaStream(file_path)
        )
        
        # Audio mute kar dete hain taaki shor na aaye
        try:
            await call_py.mute_stream(message.chat.id)
        except:
            pass
        
        await status.edit("✅ **Poster Attached.**")
        
    except Exception as e:
        await status.edit(f"❌ Error: {e}")

# 3. /leave Command
@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def stop_stream(client, message):
    if message.from_user.id not in SUDO_USERS:
        return

    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("👋 **Poster Out.**")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# --- EXECUTION ---
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Bot Starting...")
    call_py.start()
    user_bot.run()
