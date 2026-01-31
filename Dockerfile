# Python ka patla version use karenge storage bachane ke liye
FROM python:3.10-slim-buster

# System updates aur FFmpeg install karna (Ye step bohot zaroori hai VC ke liye)
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
