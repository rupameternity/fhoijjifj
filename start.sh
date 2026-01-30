#!/bin/bash

# 1. Start WARP Daemon in Background (Ye line missing thi)
echo "Starting WARP Daemon..."
warp-svc &

# 2. Wait for daemon to wake up
sleep 5

# 3. Setup WARP
echo "Registering WARP..."
mkdir -p /var/lib/cloudflare-warp
warp-cli --accept-tos registration new
warp-cli --accept-tos mode proxy

# 4. Connect
echo "Connecting to Cloudflare..."
warp-cli --accept-tos connect

# 5. Connection Check (Optional)
sleep 3
curl -s https://ifconfig.me || echo "Connection check failed, continuing..."

# 6. Start Python Bot
echo "Starting Bot..."
python3 main.py
