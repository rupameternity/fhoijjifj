FROM python:3.9-slim-bullseye

# Asli Fix: Maine 'python3-dev', 'libopus-dev', 'libsodium-dev' add kiya hai.
# Inke bina 'git' wala installation fail ho jata hai.
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    ffmpeg \
    git \
    build-essential \
    python3-dev \
    libopus-dev \
    libffi-dev \
    libsodium-dev \
    && apt-get clean

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x start.sh

CMD ["./start.sh"]
