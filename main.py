import os
import asyncio
from flask import Flask
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
import threading

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING")

# Trusted Admins ki IDs yahan daal (Comma laga ke add kar sakta hai)
AUTHORIZED_USERS = [12345678, 87654321] 

# --- FLASK KEEP-ALIVE (Render ko zinda rakhne ke liye) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "VC Shield is Active & Protected by WARP!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- BOT SETUP WITH WARP PROXY ---
# Hum force kar rahe hain ki Bot sirf WARP ke local proxy se connect ho
warp_proxy = {
    "scheme": "socks5",
    "hostname": "127.0.0.1",
    "port": 40000
}

user_bot = Client(
    "glitch_shield", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    session_string=SESSION,
    proxy=warp_proxy  # 🔒 SECURITY LOCK
)

call_py = PyTgCalls(user_bot)

# --- PERMISSION CHECK ---
async def is_authorized(message):
    # 1. Check agar user Authorized List mein hai
    if message.from_user and message.from_user.id in AUTHORIZED_USERS:
        return True
    
    # 2. Check agar user Anonymous Admin hai (Group ID = Sender ID)
    if message.sender_chat and message.sender_chat.id == message.chat.id:
        return True
        
    return False

# --- COMMANDS ---

@user_bot.on_message(filters.command(["ten_join", "join"], prefixes=["/", "!"]) & filters.group)
async def join_vc(client, message):
    if not await is_authorized(message):
        return

    chat_id = message.chat.id
    status_msg = await message.reply("Connecting via WARP Shield...")

    try:
        # 'join_as' ka matlab hai Bot 'Group' banke join karega (Anonymous)
        # Audio link silent hai, bas connection hold karne ke liye
        await call_py.join_group_call(
            chat_id, 
            AudioPiped("http://docs.evostream.com/sample_content/assets/sintel1min720p.mkv"),
            join_as=await client.resolve_peer(chat_id)
        )
        await status_msg.edit("**Shield Activated!**\nJoined as Anonymous Admin.\nIP is Masked via Cloudflare.")
    except Exception as e:
        await status_msg.edit(f"❌ Error: {e}")

@user_bot.on_message(filters.command(["ten_leave", "leave"], prefixes=["/", "!"]) & filters.group)
async def leave_vc(client, message):
    if not await is_authorized(message):
        return

    chat_id = message.chat.id
    try:
        await call_py.leave_group_call(chat_id)
        await message.reply("👋 Shield Deactivated.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# --- STARTUP ---
if __name__ == "__main__":
    # Flask ko background mein chalana
    threading.Thread(target=run_flask).start()
    
    # Bot start karna
    print("Starting Cloudflare WARP Shielded Bot...")
    call_py.start()
    print("Bot is Running...")
    user_bot.run()