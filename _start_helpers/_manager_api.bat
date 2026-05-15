@echo off
title [API] Manager API - port 8002
color 0E
cd /d "D:\Intern2026\esp32_server\esp32-server\main\manager-api"
mvn spring-boot:run -Dspring-boot.run.jvmArguments="-Dfile.encoding=UTF-8"
echo.
echo [ERR] Manager API exited.
pause
