@echo off
echo Preparing deployment package...

REM Create deployment directory
mkdir trading-bot 2>nul

REM Copy main application files
copy ..\app.py trading-bot\
copy ..\requirements.txt trading-bot\
copy ..\*.py trading-bot\

REM Copy configuration (excluding sensitive data)
mkdir trading-bot\config 2>nul
copy ..\config\trading_config.json trading-bot\config\

REM Copy templates and static files
xcopy /E /I ..\templates trading-bot\templates
xcopy /E /I ..\static trading-bot\static

REM Copy trading engine
xcopy /E /I ..\trading trading-bot\trading

REM Create necessary directories
mkdir trading-bot\database 2>nul
mkdir trading-bot\logs 2>nul
mkdir trading-bot\dashboard_data 2>nul

REM Copy deployment files
copy Dockerfile trading-bot\
copy docker-compose.yml trading-bot\
copy .dockerignore trading-bot\
copy README.md trading-bot\

REM Create a clean .env.example file
echo COINGECKO_API_KEY=your_api_key_here > trading-bot\.env.example
echo PHANTOM_WALLET=your_wallet_address_here >> trading-bot\.env.example

echo Deployment package prepared in the trading-bot directory
echo Please review the contents before deploying to DigitalOcean
pause
