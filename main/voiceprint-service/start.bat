@echo off
title [VOICE] Voiceprint Service - port 8100
color 0D
cd /d "%~dp0"
call conda activate xiaozhi-esp32-server
if errorlevel 1 (
    echo [ERROR] Conda env "xiaozhi-esp32-server" not found.
    pause
    exit /b 1
)
echo Starting Voiceprint Service...
python app.py
pause
