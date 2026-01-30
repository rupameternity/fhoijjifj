FROM python:3.10-bullseye

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
RUN pip install --no-cache-dir -U -r requirements.txt
RUN chmod +x start.sh
CMD ["./start.sh"]
