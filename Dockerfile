FROM python:3.9-slim-bullseye

# 1. Install Dependencies (Git add kar diya hai yahan)
RUN apt-get update && apt-get install -y curl gnupg lsb-release ffmpeg git && \
    curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | gpg --dearmor -o /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/cloudflare-client.list && \
    apt-get update && \
    apt-get install -y cloudflare-warp

# 2. Work Directory
WORKDIR /app
COPY . .

# 3. Requirements Install
RUN pip install --no-cache-dir -r requirements.txt

# 4. Permissions
RUN chmod +x start.sh

# 5. Start
CMD ["./start.sh"]
