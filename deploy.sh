#!/bin/bash

# Pull latest changes
git pull

# Build new image
docker build -t memehunter:latest .

# Stop existing container
docker stop memehunter || true
docker rm memehunter || true

# Run new container
docker run -d \
    --name memehunter \
    --restart unless-stopped \
    -v /app/data:/app/data \
    memehunter:latest
