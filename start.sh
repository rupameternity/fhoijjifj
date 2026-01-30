#!/bin/bash

# 1. WARP Register aur Mode set karna
echo "Setting up WARP..."
mkdir -p /var/lib/cloudflare-warp
warp-cli --accept-tos registration new
warp-cli --accept-tos mode proxy

# 2. Connect karna
echo "Connecting to Cloudflare Network..."
warp-cli --accept-tos connect

# 3. Connection confirm hone ka wait karna
sleep 5

# 4. Python Bot Start
echo "Starting Python Script..."
python3 main.py