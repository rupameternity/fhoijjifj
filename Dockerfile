# 'slim' hata diya hai, ab full version use kar rahe hain
FROM python:3.9-bullseye

# Sirf FFmpeg chahiye (Audio ke liye zaroori hai)
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x start.sh

CMD ["./start.sh"]
