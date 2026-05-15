@echo off
title [SERVER] Xiaozhi AI - port 8000
color 09
cd /d "%~dp0"
call conda activate xiaozhi-esp32-server
if errorlevel 1 (
    echo [ERROR] Conda env "xiaozhi-esp32-server" not found.
    pause
    exit /b 1
)
echo Starting Xiaozhi Server...
python app.py
pause
