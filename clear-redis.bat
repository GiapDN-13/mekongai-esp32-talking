@echo off
REM ============================================================================
REM  Clear Redis cache — use when Redis causes connection/data errors
REM  Flushes all Redis data and optionally removes persistence files.
REM ============================================================================

echo.
echo === Redis Cache Cleaner ===
echo.

REM Try to flush via redis-cli inside Docker container
echo [1/3] Attempting FLUSHALL via Docker redis-cli...
docker compose -f "%~dp0main\xiaozhi-server\docker-compose.yml" exec redis redis-cli -a xiaozhi_redis_2024 FLUSHALL 2>nul && (
    echo   -^> FLUSHALL OK
) || (
    echo   -^> FLUSHALL failed or Redis not running
)

REM Remove persistence files on disk
echo [2/3] Removing Redis persistence files...
set REDIS_DIR=%~dp0main\xiaozhi-server\data\redis
if exist "%REDIS_DIR%" (
    rd /s /q "%REDIS_DIR%" 2>nul
    mkdir "%REDIS_DIR%" 2>nul
    echo   -^> Cleared: %REDIS_DIR%
) else (
    echo   -^> Directory not found: %REDIS_DIR%
)

REM Restart Redis container
echo [3/3] Restarting Redis container...
docker compose -f "%~dp0main\xiaozhi-server\docker-compose.yml" restart redis 2>nul && (
    echo   -^> Redis restarted.
) || (
    echo   -^> Redis not running. Start with: docker compose up -d redis
)

echo.
echo === Done. Redis cache cleared. ===
echo.
pause
