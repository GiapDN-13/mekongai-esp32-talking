@echo off
echo ============================================
echo   Voiceprint Service - Stopping...
echo ============================================
echo.

for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8100" ^| findstr "LISTENING"') do (
    echo [INFO] Found voiceprint service PID: %%a
    taskkill /F /PID %%a
    if errorlevel 1 (
        echo [WARN] Could not kill PID %%a
    ) else (
        echo [OK] Process %%a terminated.
    )
    goto :done
)

echo [INFO] No process found listening on port 8100.

:done
echo.
echo Done.
timeout /t 3
