# Note: Humne 'slim' hata diya hai. Ye Full Version hai.
FROM python:3.9

# Audio Libraries aur FFmpeg install kar rahe hain
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus-dev \
    libsodium-dev \
    git \
    && apt-get clean

WORKDIR /app
COPY . .

# Ab pip install fail nahi hoga kyunki saare tools maujood hain
RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x start.sh

CMD ["./start.sh"]
