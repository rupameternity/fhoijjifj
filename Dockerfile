FROM python:3.9-slim-bullseye

WORKDIR /app

# System Update & FFmpeg (Audio ke liye zaroori hai)
RUN apt-get update && apt-get install -y ffmpeg git && apt-get clean

COPY . .

# Requirements Install
RUN pip install --no-cache-dir -r requirements.txt

# Start Script Permission
RUN chmod +x start.sh

CMD ["./start.sh"]
