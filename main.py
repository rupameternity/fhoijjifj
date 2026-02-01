import os
import threading
import asyncio
from flask import Flask

# --- THE PATCH (Jo error fix karega) ---
# Ye code sabse upar hona zaroori hai
import pyrogram.errors
class FakeError(Exception):
    pass

# Dono spelling assign kar rahe hain taaki crash na ho
pyrogram.errors.GroupCallForbidden = FakeError
pyrogram.errors.GroupcallForbidden = FakeError
# ---------------------------------------

from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# --- CONFIGURATION (Render Env Vars se) ---
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SESSION = os.environ.get("SESSION_STRING", "")

# Env vars ko list mein convert karna
ALLOWED_GROUPS = [int(x.strip()) for x in os.environ.get("ALLOWED_GROUPS", "").split(",") if x.strip()]
SUDO_USERS = [int(x.strip()) for x in os.environ.get("SUDO_USERS", "").split(",") if x.strip()]

# --- FLASK SERVER (Render ko zinda rakhne ke liye) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Poster Bot is Running with Patch!"

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
    # Agar allowed group nahi hai, toh check karo
    if message.chat.id not in ALLOWED_GROUPS:
        try:
            # Leave message
            await message.reply("❌ Unauthorized Group. Leaving...")
            await client.leave_chat(message.chat.id)
        except:
            pass
        return
    message.continue_propagation()

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
        await call_py.play(
            message.chat.id, 
            MediaStream(
                file_path,
                video_flags=MediaStream.Flags.IGNORE_AUDIO # Sirf video/image dikhana hai
            )
        )
        
        await status.edit("✅ **Poster Attached.**")
        
        # Optional: File delete mat karna abhi, stream ke liye chahiye hoti hai
        
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
    # Flask ko alag thread mein chalayenge
    threading.Thread(target=run_flask).start()
    
    # Bot ko start karenge
    print("Bot Starting...")
    call_py.start()
    user_bot.run()
