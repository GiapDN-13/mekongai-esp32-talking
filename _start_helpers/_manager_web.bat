@echo off
title [WEB] Manager Web - port 8001
color 0A
cd /d "D:\Intern2026\esp32_server\esp32-server\main\manager-web"
set NODE_OPTIONS=--localstorage-file=node_localstorage
npm run serve
echo.
echo [ERR] Manager Web exited.
pause
