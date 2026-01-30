FROM python:3.10-bullseye

# 'build-essential' aur 'python3-dev' add kiya hai. 
# Ye bahut zaroori hai GitHub se library install karne ke liye.
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    libopus-dev \
    libsodium-dev \
    python3-dev \
    && apt-get clean

WORKDIR /app
COPY . .

# Cache clear karke install karenge
RUN pip install --no-cache-dir -U -r requirements.txt
RUN chmod +x start.sh

CMD ["./start.sh"]
