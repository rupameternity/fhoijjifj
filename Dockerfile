FROM python:3.10-bullseye

# Network aur Audio drivers install kar rahe hain
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    libopus-dev \
    libsodium-dev \
    python3-dev \
    iputils-ping \
    && apt-get clean

WORKDIR /app
COPY . .

# Cache clear karke fresh install
RUN pip install --no-cache-dir -U -r requirements.txt
RUN chmod +x start.sh

CMD ["./start.sh"]
