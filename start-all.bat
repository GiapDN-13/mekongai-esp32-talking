@echo off
REM ============================================================================
REM  Xiaozhi ESP32 Server — Start All Services (Windows)
REM
REM  Prerequisites:
REM    - Docker Desktop running
REM    - Conda env "xiaozhi-esp32-server" (Python 3.10)
REM    - Java 21 + Maven
REM    - Node.js + npm (manager-web/node_modules installed)
REM
REM  Usage:
REM    start-all.bat                Start all services
REM    start-all.bat --no-web       Skip manager-web dev server
REM    start-all.bat --no-portal    Skip teacher-portal dev server
REM ============================================================================

setlocal EnableDelayedExpansion

set "ROOT=%~dp0"
set "CONDA_ENV=xiaozhi-esp32-server"
set "HELPER_DIR=%ROOT%_start_helpers"

cls
echo.
echo  ========================================================
echo          XIAOZHI ESP32 — Service Launcher
echo  ========================================================
echo.

REM --- Generate helper scripts (avoids nested-quote issues in `start cmd /k`) ---
if not exist "%HELPER_DIR%" mkdir "%HELPER_DIR%"

> "%HELPER_DIR%\_voiceprint.bat" (
    echo @echo off
    echo title [VOICE] Voiceprint Service - port 8100
    echo color 0D
    echo cd /d "%ROOT%main\voiceprint-service"
    echo call conda activate %CONDA_ENV%
    echo echo.
    echo echo Starting Voiceprint Service...
    echo python app.py
    echo echo.
    echo echo [ERR] Voiceprint Service exited.
    echo pause
)

> "%HELPER_DIR%\_manager_api.bat" (
    echo @echo off
    echo title [API] Manager API - port 8002
    echo color 0E
    echo cd /d "%ROOT%main\manager-api"
    echo mvn spring-boot:run -Dspring-boot.run.jvmArguments="-Dfile.encoding=UTF-8"
    echo echo.
    echo echo [ERR] Manager API exited.
    echo pause
)

> "%HELPER_DIR%\_manager_web.bat" (
    echo @echo off
    echo title [WEB] Manager Web - port 8001
    echo color 0A
    echo cd /d "%ROOT%main\manager-web"
    echo set NODE_OPTIONS=--localstorage-file=node_localstorage
    echo npm run serve
    echo echo.
    echo echo [ERR] Manager Web exited.
    echo pause
)

> "%HELPER_DIR%\_xiaozhi_server.bat" (
    echo @echo off
    echo title [SERVER] Xiaozhi AI - port 8000
    echo color 09
    echo cd /d "%ROOT%main\xiaozhi-server"
    echo call conda activate %CONDA_ENV%
    echo set XIAOZHI_CONFIG_PROFILE=storyteller
    echo echo.
    echo echo Starting Xiaozhi Server [storyteller profile]...
    echo python app.py
    echo echo.
    echo echo [ERR] Xiaozhi Server exited.
    echo pause
)

> "%HELPER_DIR%\_teacher_portal.bat" (
    echo @echo off
    echo title [PORTAL] Teacher Portal - port 3000
    echo color 0B
    echo cd /d "%ROOT%main\teacher-portal"
    echo if not exist node_modules (
    echo     echo Installing dependencies...
    echo     call npm install
    echo )
    echo echo.
    echo echo Starting Teacher Portal...
    echo npm run dev
    echo echo.
    echo echo [ERR] Teacher Portal exited.
    echo pause
)

REM ---------------------------------------------------------------
REM  1. Docker Infrastructure (MySQL 3307, Redis 6379, Qdrant 6333)
REM ---------------------------------------------------------------
echo  [1/6] Docker Infrastructure
echo  -------------------------------------------------
cd /d "%ROOT%main\xiaozhi-server"
docker compose up -d mysql redis qdrant
if !ERRORLEVEL! NEQ 0 (
    echo  [ERR] Docker failed. Is Docker Desktop running?
    pause
    exit /b 1
)
echo  [OK]  Docker services started.
echo        Waiting 8s for MySQL to become healthy...
timeout /t 8 /nobreak > nul

REM ---------------------------------------------------------------
REM  2. Voiceprint Service (port 8100)
REM ---------------------------------------------------------------
echo.
echo  [2/6] Voiceprint Service (port 8100)
echo  -------------------------------------------------
call :free_port 8100 "Voiceprint Service"
start "VOICE-Voiceprint" cmd /k "%HELPER_DIR%\_voiceprint.bat"
echo  [OK]  Voiceprint Service starting... (magenta window)
timeout /t 3 /nobreak > nul

REM ---------------------------------------------------------------
REM  3. Manager API (port 8002) — must start BEFORE Manager Web
REM ---------------------------------------------------------------
echo.
echo  [3/6] Manager API (port 8002)
echo  -------------------------------------------------
netstat -ano | findstr ":8002.*LISTENING" > nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo  [OK]  Manager API already running on port 8002.
    goto api_ready
)
where mvn > nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo  [SKIP] mvn not found. Install Maven to run Manager API.
    goto skip_api
)
start "API-ManagerAPI" cmd /k "%HELPER_DIR%\_manager_api.bat"
echo  [OK]  Manager API starting... (yellow window)
echo        Waiting for Tomcat on port 8002...

REM Poll until port 8002 is listening (max 120 seconds)
set "wait_count=0"
:wait_api
timeout /t 3 /nobreak > nul
set /a wait_count+=3
netstat -ano | findstr ":8002.*LISTENING" > nul 2>&1
if !ERRORLEVEL! EQU 0 goto api_ready
if !wait_count! GEQ 120 (
    echo  [WARN] Manager API did not start within 120s. Continuing anyway...
    goto skip_api
)
echo        ... waiting (!wait_count!s)
goto wait_api

:api_ready
echo  [OK]  Manager API is ready on port 8002.
:skip_api

REM ---------------------------------------------------------------
REM  4. Manager Web (port 8001)
REM ---------------------------------------------------------------
if "%~1"=="--no-web" goto skip_web
echo.
echo  [4/6] Manager Web (port 8001)
echo  -------------------------------------------------
netstat -ano | findstr ":8001.*LISTENING" > nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo  [OK]  Manager Web already running on port 8001.
    goto skip_web
)
where npm > nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo  [SKIP] npm not found.
    goto skip_web
)
if not exist "%ROOT%main\manager-web\node_modules" (
    echo  [..] Installing npm dependencies first run...
    cd /d "%ROOT%main\manager-web"
    call npm install --legacy-peer-deps
)
start "WEB-ManagerWeb" cmd /k "%HELPER_DIR%\_manager_web.bat"
echo  [OK]  Manager Web starting... (green window)
:skip_web

REM ---------------------------------------------------------------
REM  5. Xiaozhi Server (port 8000 WS + 8003 HTTP)
REM ---------------------------------------------------------------
echo.
echo  [5/6] Xiaozhi Server (port 8000)
echo  -------------------------------------------------
call :free_port 8000 "Xiaozhi Server"
call :free_port 8003 "Xiaozhi HTTP"
start "SERVER-XiaozhiAI" cmd /k "%HELPER_DIR%\_xiaozhi_server.bat"
echo  [OK]  Xiaozhi Server starting... (blue window)

REM ---------------------------------------------------------------
REM  6. Teacher Portal (port 3000)
REM ---------------------------------------------------------------
if "%~1"=="--no-portal" goto skip_portal
echo.
echo  [6/6] Teacher Portal (port 3000)
echo  -------------------------------------------------
netstat -ano | findstr ":3000.*LISTENING" > nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo  [OK]  Teacher Portal already running on port 3000.
    goto skip_portal
)
where npm > nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo  [SKIP] npm not found.
    goto skip_portal
)
start "PORTAL-TeacherPortal" cmd /k "%HELPER_DIR%\_teacher_portal.bat"
echo  [OK]  Teacher Portal starting... (cyan window)
:skip_portal

REM ---------------------------------------------------------------
REM  Summary
REM ---------------------------------------------------------------
echo.
echo  =========================================================
echo   All services launched!
echo  =========================================================
echo.
echo   Service               Port   Window Color
echo   ---------------------------------------------------------
echo   [DOCKER] MySQL        3307   (container)
echo   [DOCKER] Redis        6379   (container)
echo   [DOCKER] Qdrant       6333   (container)
echo   [VOICE ] Voiceprint   8100   magenta
echo   [API   ] Manager API  8002   yellow
echo   [WEB   ] Manager Web  8001   green
echo   [SERVER] Xiaozhi AI   8000   blue
echo   [PORTAL] Teacher      3000   cyan
echo.
echo   Admin Console:    http://localhost:8001
echo   Teacher Portal:   http://localhost:3000
echo   API Docs:         http://localhost:8002/xiaozhi/doc.html
echo   Qdrant UI:        http://localhost:6333/dashboard
echo.
echo   To stop all: run stop-all.bat
echo.
pause
goto :eof

REM ---------------------------------------------------------------
REM  Subroutine: kill process on port
REM ---------------------------------------------------------------
:free_port
set "fp_port=%~1"
set "fp_name=%~2"
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%fp_port%.*LISTENING" 2^>nul') do (
    echo  [!] Port %fp_port% in use by PID %%p - killing old %fp_name%...
    taskkill /F /PID %%p >nul 2>&1
    timeout /t 1 /nobreak >nul
)
goto :eof
