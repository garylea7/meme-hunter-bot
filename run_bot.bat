@echo off
title MemeHunter Trading Bot

REM Check if bot is already running
tasklist /FI "WINDOWTITLE eq MemeHunter Trading Bot" | find "cmd.exe" >nul
if %errorlevel% equ 0 (
    echo Bot is already running!
    echo Close the existing bot window first.
    pause
    exit
)

REM Kill any existing Python processes running qt_dashboard.py
taskkill /F /IM python.exe /FI "WINDOWTITLE eq MemeHunter Trading Bot" >nul 2>&1

REM Start the bot
python -OO qt_dashboard.py
pause
