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

# 1. ALLOWED GROUPS (Sirf inhi groups mein bot chalega)
# Environment variable se string aayegi, hum use list mein convert karenge
# Example Env Var: -10012345678, -10087654321
allowed_groups_env = os.environ.get("ALLOWED_GROUPS", "")
ALLOWED_GROUPS = [int(x.strip()) for x in allowed_groups_env.split(",") if x.strip()]

# 2. AUTHORIZED ADMINS (Jo command de sakte hain)
authorized_users_env = os.environ.get("AUTHORIZED_USERS", "")
AUTHORIZED_USERS = [int(x.strip()) for x in authorized_users_env.split(",") if x.strip()]

# --- FLASK KEEP-ALIVE ---
app = Flask(__name__)

@app.route('/')
def home():
    return "🛡️ Security Active: Group Whitelist Enabled."

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- BOT SETUP WITH WARP PROXY ---
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
    proxy=warp_proxy
)

call_py = PyTgCalls(user_bot)

# --- SECURITY CHECK ---
async def is_authorized(message):
    # Check 1: Kya ye message Group mein hai? (Private chats allowed nahi)
    if message.chat.type not in [
        message.chat.type.GROUP, 
        message.chat.type.SUPERGROUP
    ]:
        return False

    # Check 2: Kya ye Group 'ALLOWED_GROUPS' list mein hai?
    if message.chat.id not in ALLOWED_GROUPS:
        # Agar group allowed nahi hai, toh chupchap return kar do (Ignore)
        return False
    
    # Check 3: Kya User Authorized Admin hai?
    if message.from_user and message.from_user.id in AUTHORIZED_USERS:
        return True
    
    # Check 4: Kya ye Anonymous Admin hai? (Sender ID == Chat ID)
    if message.sender_chat and message.sender_chat.id == message.chat.id:
        return True
        
    return False

# --- COMMANDS ---

# filters.group laga diya taaki DMs mein command work hi na kare
@user_bot.on_message(filters.command(["ten_join", "join"], prefixes=["/", "!"]) & filters.group)
async def join_vc(client, message):
    if not await is_authorized(message):
        return

    chat_id = message.chat.id
    status_msg = await message.reply("🛡️ Verifying Group ID & Connecting...")

    try:
        await call_py.join_group_call(
            chat_id, 
            AudioPiped("http://docs.evostream.com/sample_content/assets/sintel1min720p.mkv"),
            join_as=await client.resolve_peer(chat_id)
        )
        await status_msg.edit(f"✅ **Shield Activated!**\nAuthorized Group Detected.\nIP Masked via WARP.")
    except Exception as e:
        await status_msg.edit(f"❌ Error: {e}")

@user_bot.on_message(filters.command(["ten_leave", "leave"], prefixes=["/", "!"]) & filters.group)
async def leave_vc(client, message):
    if not await is_authorized(message):
        return

    chat_id = message.chat.id
    try:
        await call_py.leave_group_call(chat_id)
        await message.reply("👋 Leaving Authorized Group.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# --- STARTUP ---
if __name__ == "__main__":
    # Print loaded settings for debugging in logs
    print(f"✅ Loaded Allowed Groups: {ALLOWED_GROUPS}")
    print(f"✅ Loaded Authorized Admins: {AUTHORIZED_USERS}")
    
    threading.Thread(target=run_flask).start()
    
    print("Starting Shield Bot...")
    call_py.start()
    user_bot.run()
