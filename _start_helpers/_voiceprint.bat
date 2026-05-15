@echo off
title [VOICE] Voiceprint Service - port 8100
color 0D
cd /d "D:\Intern2026\esp32_server\esp32-server\main\voiceprint-service"
call conda activate xiaozhi-esp32-server
echo.
echo Starting Voiceprint Service...
python app.py
echo.
echo [ERR] Voiceprint Service exited.
pause
