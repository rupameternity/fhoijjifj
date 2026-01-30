FROM python:3.9-slim-bullseye

# 1. Install Dependencies (Build Essential zaroori hai latest versions ke liye)
RUN apt-get update && apt-get install -y curl gnupg lsb-release ffmpeg git build-essential && \
    apt-get clean

# 2. Work Directory
WORKDIR /app
COPY . .

# 3. Install Python Requirements
RUN pip install --no-cache-dir -r requirements.txt

# 4. Permissions
RUN chmod +x start.sh

# 5. Start
CMD ["./start.sh"]
