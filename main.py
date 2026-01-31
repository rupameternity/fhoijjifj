import os
import asyncio
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from aiohttp import web

# ================= SECURE CONFIGURATION ================= #

# Ye values ab Environment Variables se aayengi
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")

# Lists ko comma se tod kar integer banayenge
# Example Env Var: -100123456,-100987654
ALLOWED_GROUPS = [int(x) for x in os.getenv("ALLOWED_GROUPS", "").split(",") if x.strip()]

# Example Env Var: 12345678,87654321
SUDO_USERS = [int(x) for x in os.getenv("SUDO_USERS", "").split(",") if x.strip()]

# ================= BOT SETUP ================= #

app = Client("poster_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
call_py = PyTgCalls(app)

# ================= LOGIC ================= #

# 1. Auto-Leave Logic (Security)
@app.on_message(filters.group)
async def security_check(client, message):
    chat_id = message.chat.id
    
    # Agar ALLOWED_GROUPS list khali hai ya group match nahi hota
    if chat_id not in ALLOWED_GROUPS:
        try:
            # Leave silently or with message
            await message.reply("❌ Unauthorized Group. Leaving...")
            await client.leave_chat(chat_id)
        except:
            pass
        return

    message.continue_propagation()


# 2. /go Command (Stream Photo)
@app.on_message(filters.command("go") & filters.group)
async def start_stream(client, message):
    if message.from_user.id not in SUDO_USERS:
        return 

    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("❗ Photo pe reply karke /go likho.")
        return

    try:
        status = await message.reply("🔄 Processing...")
        file_path = await message.reply_to_message.download()

        await call_py.play(
            message.chat.id,
            MediaStream(
                file_path,
                video_flags=MediaStream.Flags.IGNORE_AUDIO
            )
        )

        await status.delete()
        await message.reply("Poster attached")
        # os.remove(file_path) # Optional: Delete local file

    except Exception as e:
        await message.reply(f"❌ Error: {e}")


# 3. /leave Command (Stop Stream)
@app.on_message(filters.command("leave") & filters.group)
async def stop_stream(client, message):
    if message.from_user.id not in SUDO_USERS:
        return

    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("Poster out")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


# ================= RENDER KEEP-ALIVE SERVER ================= #

async def web_server():
    async def handle(request):
        return web.Response(text="Secure Poster Bot Running!")

    app_web = web.Application()
    app_web.router.add_get('/', handle)
    runner = web.AppRunner(app_web)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# ================= MAIN EXECUTION ================= #

async def main():
    if not API_ID or not SESSION_STRING:
        print("❌ Error: Environment Variables set nahi hain!")
        return

    print("Starting Services...")
    await web_server()
    await app.start()
    await call_py.start()
    print("Bot Started Successfully!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
