@echo off
title ThreatVision - Shutdown
color 0C

echo.
echo  Stopping ThreatVision services...
echo.

:: Kill backend (uvicorn on 8001)
echo  [1/3] Stopping Backend...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8001 " ^| findstr "LISTENING" 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo   [OK] Backend stopped.

:: Kill frontend (Next.js on 3001)
echo  [2/3] Stopping Frontend...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3001 " ^| findstr "LISTENING" 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo   [OK] Frontend stopped.

:: Stop Docker Postgres
echo  [3/3] Stopping PostgreSQL...
cd /d "%~dp0"
docker compose down 2>nul
echo   [OK] PostgreSQL stopped.

echo.
echo  All services stopped.
echo.
pause
