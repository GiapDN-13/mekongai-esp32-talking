@echo off
REM ============================================================================
REM  Xiaozhi ESP32 Server — Stop All Services (Windows)
REM ============================================================================

setlocal EnableDelayedExpansion

echo.
echo  ========================================================
echo          XIAOZHI ESP32 — Stopping Services
echo  ========================================================
echo.

REM Kill services by port (Python, Node)
call :kill_port 8100 "Voiceprint Service"
call :kill_port 8000 "Xiaozhi Server"
call :kill_port 8003 "Xiaozhi HTTP API"
call :kill_port 8001 "Manager Web"

REM Manager API (Java/Maven) needs special handling:
REM  mvn spring-boot:run spawns a child JVM. Kill both the port holder
REM  and any lingering java processes with xiaozhi in the classpath.
call :kill_port 8002 "Manager API"
for /f "tokens=2" %%p in ('tasklist /fi "imagename eq java.exe" /fo list 2^>nul ^| findstr "PID:"') do (
    wmic process where "ProcessId=%%p" get CommandLine 2>nul | findstr /i "xiaozhi-esp32-api" >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        echo  [!] Killing lingering Java process PID %%p (manager-api)
        taskkill /F /PID %%p >nul 2>&1
    )
)

REM Close any leftover cmd windows opened by start-all.bat
for %%t in (VOICE-Voiceprint API-ManagerAPI WEB-ManagerWeb SERVER-XiaozhiAI) do (
    taskkill /FI "WINDOWTITLE eq %%t*" /F >nul 2>&1
)

echo.
set /p STOP_DOCKER="  Stop Docker containers too? (y/N): "
if /i "%STOP_DOCKER%"=="y" (
    cd /d "%~dp0main\xiaozhi-server"
    docker compose stop
    echo  [OK] Docker containers stopped.
) else (
    echo  [--] Docker containers left running.
)

echo.
echo  =========================================================
echo   All services stopped.
echo  =========================================================
echo.
pause
goto :eof

REM ---------------------------------------------------------------
REM  Subroutine: kill process listening on a port
REM ---------------------------------------------------------------
:kill_port
set "kp_port=%~1"
set "kp_name=%~2"
set "found=0"
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%kp_port%.*LISTENING" 2^>nul') do (
    taskkill /F /PID %%p >nul 2>&1
    echo  [OK] %kp_name% (port %kp_port%, PID %%p) stopped.
    set "found=1"
)
if "!found!"=="0" echo  [--] %kp_name% (port %kp_port%) not running.
goto :eof
