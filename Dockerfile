# Buster hata ke 'slim-bookworm' use kar rahe hain (Latest Stable Debian)
FROM python:3.10-slim-bookworm

# System updates aur FFmpeg install karna
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

# Working Directory set karna
WORKDIR /app

# Requirements install karna
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Saara code copy karna
COPY . .

# Bot start karna
CMD ["python3", "main.py"]
