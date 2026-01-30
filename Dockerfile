FROM python:3.9-slim-bullseye

# git aur build-essential zaroori hain GitHub se install karne ke liye
RUN apt-get update && apt-get install -y curl gnupg lsb-release ffmpeg git build-essential && \
    apt-get clean

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x start.sh
CMD ["./start.sh"]
