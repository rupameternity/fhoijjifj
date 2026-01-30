# FIX: Version 3.10 kar diya hai kyunki library ko yehi chahiye
FROM python:3.10-bullseye

# System Tools install kar rahe hain
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus-dev \
    libsodium-dev \
    git \
    && apt-get clean

WORKDIR /app
COPY . .

# Ab pip fail nahi hoga kyunki Python version sahi hai
RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x start.sh

CMD ["./start.sh"]
