import os
import asyncio
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# --- Configuration from Render Environment Variables ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")

# Admin aur Groups ko comma se split karke list banayenge
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]
ALLOWED_GROUPS = [int(x) for x in os.environ.get("ALLOWED_GROUPS", "").split(",") if x.strip()]

# --- Client Setup ---
app = Client(
    "render_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)
call_py = PyTgCalls(app)

# --- Helper Function to Clean Cache ---
def clean_cache():
    if os.path.exists("input.jpg"):
        os.remove("input.jpg")
    if os.path.exists("stream.mp4"):
        os.remove("stream.mp4")

# --- /go Command Handler ---
@app.on_message(filters.command("go") & filters.group)
async def start_stream(client, message):
    # Security Check: Only Admin & Allowed Groups
    if message.from_user.id not in ADMIN_IDS:
        return
    if message.chat.id not in ALLOWED_GROUPS:
        return

    # Check if replied to a photo
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text("❌ Bhai kisi photo pe reply karke /go likh.")
        return

    status_msg = await message.reply_text("🔄 Processing... Photo download kar raha hun.")

    # Purana kachra saaf karo
    clean_cache()

    try:
        # 1. Download Photo
        await message.reply_to_message.download("input.jpg")
        await status_msg.edit("🎬 Video generate kar raha hun (FFMPEG)...")

        # 2. Convert Image to Video using FFMPEG (Lightweight Loop)
        # -loop 1: Image loop karega
        # -t 3600: 1 ghante ki stream banayega (file size control ke liye)
        # -pix_fmt yuv420p: Telegram support ke liye zaroori hai
        # -r 10: Sirf 10 FPS (Static image hai, high FPS ki zaroorat nahi, RAM bachega)
        ffmpeg_cmd = (
            "ffmpeg -loop 1 -i input.jpg -f lavfi -i anullsrc "
            "-c:v libx264 -tune stillimage -c:a aac -b:a 12k "
            "-pix_fmt yuv420p -r 10 -shortest -t 3600 stream.mp4 -y"
        )
        
        process = await asyncio.create_subprocess_shell(ffmpeg_cmd)
        await process.communicate()

        # 3. Join VC and Stream
        if not os.path.exists("stream.mp4"):
            await status_msg.edit("❌ Error: Video file create nahi hui.")
            return

        await status_msg.edit("▶️ Streaming starting on VC...")
        
        await call_py.play(
            message.chat.id,
            MediaStream(
                "stream.mp4",
            )
        )
        await status_msg.edit("✅ **Streaming Started!**")

    except Exception as e:
        await status_msg.edit(f"❌ Error: {e}")
        clean_cache()

# --- /leave Command Handler ---
@app.on_message(filters.command("leave") & filters.group)
async def stop_stream(client, message):
    # Security Check
    if message.from_user.id not in ADMIN_IDS:
        return
    if message.chat.id not in ALLOWED_GROUPS:
        return

    try:
        await call_py.leave_call(message.chat.id)
        await message.reply_text("👋 Left VC.")
    except Exception as e:
        await message.reply_text(f"⚠️ VC mein nahi tha shayad: {e}")

    # RAM/Disk Cleanup: Delete files immediately
    clean_cache()
    await message.reply_text("🗑️ Cache cleared. RAM free kar diya.")

# --- Start Bot ---
async def start_bot():
    print("Userbot Starting...")
    await app.start()
    await call_py.start()
    print("Userbot is Active!")
    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(start_bot())
