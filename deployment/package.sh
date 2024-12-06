#!/bin/bash

# Create deployment directory structure
mkdir -p trading-bot/{app,config,database,templates,trading}

# Copy main application files
cp ../app.py trading-bot/app.py
cp ../requirements.txt trading-bot/requirements.txt

# Copy configuration
cp ../config/trading_config.json trading-bot/config/

# Copy templates
cp ../templates/dashboard.html trading-bot/templates/

# Copy trading engine
cp ../trading/engine.py trading-bot/trading/

# Copy deployment files
cp Dockerfile trading-bot/
cp docker-compose.yml trading-bot/
cp .dockerignore trading-bot/
cp README.md trading-bot/

# Create zip archive
zip -r trading-bot.zip trading-bot/

echo "Deployment package created: trading-bot.zip"
