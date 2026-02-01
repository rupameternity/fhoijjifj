import os
import threading
import asyncio
from flask import Flask

# --- 1. CRASH FIX PATCH (Ye zaroori hai) ---
import pyrogram.errors
class FakeError(Exception):
    pass
pyrogram.errors.GroupCallForbidden = FakeError
pyrogram.errors.GroupcallForbidden = FakeError
# -------------------------------------------

from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# --- 2. CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SESSION = os.environ.get("SESSION_STRING", "")

try:
    ALLOWED_GROUPS = [int(x.strip()) for x in os.environ.get("ALLOWED_GROUPS", "").split(",") if x.strip()]
    SUDO_USERS = [int(x.strip()) for x in os.environ.get("SUDO_USERS", "").split(",") if x.strip()]
except:
    ALLOWED_GROUPS = []
    SUDO_USERS = []

# --- 3. FLASK SERVER (Port Busy Fix) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running!"

def run_flask():
    # use_reloader=False bohot zaroori hai, warna Render 2 baar chala deta hai aur port busy ho jata hai
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False) 

# --- 4. BOT SETUP ---
user_bot = Client("poster_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(user_bot)

# --- 5. LOGIC (No Conversion Mode) ---

@user_bot.on_message(filters.command(["go"], prefixes=["/", "!"]) & filters.group)
async def start_stream(client, message):
    # Security Check
    if message.from_user.id not in SUDO_USERS:
        return
    if message.chat.id not in ALLOWED_GROUPS:
        await message.reply("❌ Group Not Allowed")
        return

    # Photo Check
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("❗ Photo pe reply karo.")
        return

    status = await message.reply("⚡ **Starting Stream...**")

    try:
        # Purana call leave karo agar fasa hua hai
        try:
            await call_py.leave_call(message.chat.id)
            await asyncio.sleep(1) # Thoda saans lene do bot ko
        except:
            pass

        # 1. Download Photo
        file_path = await message.reply_to_message.download()
        
        # 2. DIRECT STREAM (No Video Conversion)
        # Hum 'MediaStream' mein photo daalenge lekin parameters change karke
        # Isse PyTgCalls khud handle karega, hum convert nahi karenge.
        
        await call_py.play(
            message.chat.id,
            MediaStream(
                file_path, 
                video_flags=MediaStream.Flags.IGNORE_AUDIO # Audio ignore karo (Fast)
            )
        )
        
        # 3. Success
        await status.edit("✅ **Poster Live!**")
        
        # Note: File delete mat karna, jab tak stream chal rahi hai file chahiye
        
    except Exception as e:
        # Agar error aaye toh print karo taaki pata chale
        print(f"Error in /go: {e}")
        await status.edit(f"❌ Error: {e}")


@user_bot.on_message(filters.command(["leave"], prefixes=["/", "!"]) & filters.group)
async def stop_stream(client, message):
    if message.from_user.id not in SUDO_USERS: return
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("👋 **Poster Out.**")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


# --- 6. MAIN EXECUTION ---
async def main():
    print("🚀 Starting Bot...")
    await user_bot.start()
    await call_py.start()
    print("✅ Bot Joined & Ready!")
    await idle()
    await call_py.stop()
    await user_bot.stop()

if __name__ == "__main__":
    # Flask ko alag thread mein bina reloader ke chalayenge
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
