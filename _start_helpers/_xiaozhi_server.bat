@echo off
title [SERVER] Xiaozhi AI - port 8000
color 09
cd /d "D:\Intern2026\esp32_server\esp32-server\main\xiaozhi-server"
call conda activate xiaozhi-esp32-server
set XIAOZHI_CONFIG_PROFILE=storyteller
echo.
echo Starting Xiaozhi Server [storyteller profile]...
python app.py
echo.
echo [ERR] Xiaozhi Server exited.
pause
