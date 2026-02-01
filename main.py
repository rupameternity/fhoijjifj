import os
import asyncio
import tempfile
import shutil
import subprocess

from telethon import TelegramClient, events
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import InputStream
from pytgcalls.types.input_stream.quality import HighQualityVideo
from PIL import Image

# ================== ENV ==================

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(",")))
ALLOWED_GROUPS = list(map(int, os.getenv("ALLOWED_GROUPS").split(",")))

# ================= CLIENT =================

client = TelegramClient(
    session=SESSION_STRING,
    api_id=API_ID,
    api_hash=API_HASH
)

vc = PyTgCalls(client)

STREAM_PROCESS = None
TEMP_DIR = None

# ================= CLEANUP =================

def clean_all():
    global STREAM_PROCESS, TEMP_DIR

    if STREAM_PROCESS:
        try:
            STREAM_PROCESS.kill()
        except:
            pass
        STREAM_PROCESS = None

    if TEMP_DIR and os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

    TEMP_DIR = None

# ================= /GO =================

@client.on(events.NewMessage(pattern=r"^/go$"))
async def start_stream(event):
    global STREAM_PROCESS, TEMP_DIR

    if event.sender_id not in ADMIN_IDS:
        return

    if event.chat_id not in ALLOWED_GROUPS:
        return

    if not event.is_group:
        return

    if not event.reply_to_msg_id:
        await event.reply("❌ Reply to an image.")
        return

    reply = await event.get_reply_message()

    if not reply.photo:
        await event.reply("❌ Only image supported.")
        return

    clean_all()

    TEMP_DIR = tempfile.mkdtemp()
    img_path = os.path.join(TEMP_DIR, "image.jpg")

    await reply.download_media(img_path)

    Image.open(img_path).convert("RGB").save(img_path)

    ffmpeg_cmd = [
        "ffmpeg",
        "-re",
        "-loop", "1",
        "-i", img_path,
        "-f", "lavfi",
        "-i", "anullsrc",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        "-"
    ]

    STREAM_PROCESS = subprocess.Popen(
        ffmpeg_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )

    await vc.join_group_call(
        event.chat_id,
        InputStream(
            STREAM_PROCESS.stdout,
            HighQualityVideo()
        )
    )

    await event.reply("🟢 Image streaming started (unlimited).")

# ================= /LEAVE =================

@client.on(events.NewMessage(pattern=r"^/leave$"))
async def stop_stream(event):
    if event.sender_id not in ADMIN_IDS:
        return

    if event.chat_id not in ALLOWED_GROUPS:
        return

    try:
        await vc.leave_group_call(event.chat_id)
    except:
        pass

    clean_all()
    await event.reply("🔴 VC left & memory cleaned.")

# ================= START =================

async def main():
    await client.start()
    await vc.start()
    print("Userbot is running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
