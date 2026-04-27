@echo off
title ThreatVision - One Click Launcher
color 0A

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║                                                              ║
echo  ║        ████████╗██╗  ██╗██████╗ ███████╗ █████╗ ████████╗    ║
echo  ║        ╚══██╔══╝██║  ██║██╔══██╗██╔════╝██╔══██╗╚══██╔══╝   ║
echo  ║           ██║   ███████║██████╔╝█████╗  ███████║   ██║       ║
echo  ║           ██║   ██╔══██║██╔══██╗██╔══╝  ██╔══██║   ██║       ║
echo  ║           ██║   ██║  ██║██║  ██║███████╗██║  ██║   ██║       ║
echo  ║           ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝    ║
echo  ║                   V I S I O N                                ║
echo  ║                                                              ║
echo  ║            Single Click Launcher by Saichandram              ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

:: ─────────────────────────────────────────────────
:: Step 1: Check prerequisites
:: ─────────────────────────────────────────────────
echo [1/6] Checking prerequisites...

where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERROR] Docker not found! Install Docker Desktop first.
    pause
    exit /b 1
)

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERROR] Node.js not found! Install Node.js 20+ first.
    pause
    exit /b 1
)

if not exist "backend\.venv\Scripts\python.exe" (
    echo   [ERROR] Python venv not found at backend\.venv
    echo          Run: cd backend ^&^& python -m venv .venv ^&^& .venv\Scripts\pip install -e ".[dev]"
    pause
    exit /b 1
)

echo   [OK] Docker, Node.js, Python venv found.
echo.

:: ─────────────────────────────────────────────────
:: Step 2: Start Postgres (Docker)
:: ─────────────────────────────────────────────────
echo [2/6] Starting PostgreSQL via Docker...
docker compose up -d 2>nul
if %errorlevel% neq 0 (
    echo   [WARN] Docker compose failed. Is Docker Desktop running?
    echo          Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo          Waiting 30s for Docker...
    timeout /t 30 /nobreak >nul
    docker compose up -d
    if %errorlevel% neq 0 (
        echo   [ERROR] Docker still not ready. Start Docker Desktop manually and re-run.
        pause
        exit /b 1
    )
)
echo   [OK] PostgreSQL container running on port 55432.
echo   Waiting for Postgres to be ready...
timeout /t 6 /nobreak >nul
echo.

:: ─────────────────────────────────────────────────
:: Step 3: Run database migrations
:: ─────────────────────────────────────────────────
echo [3/6] Applying database migrations...
"backend\.venv\Scripts\python.exe" "backend\scripts\apply_migrations.py" 2>nul
if %errorlevel% neq 0 (
    echo   [INFO] Migrations may already be applied - continuing...
)
echo   [OK] Database ready.
echo.

:: ─────────────────────────────────────────────────
:: Step 4: Install frontend deps (if needed)
:: ─────────────────────────────────────────────────
echo [4/6] Checking frontend dependencies...
if not exist "frontend\node_modules" (
    echo   Installing npm packages...
    cd frontend
    call npm install
    cd ..
)
echo   [OK] Frontend dependencies ready.
echo.

:: ─────────────────────────────────────────────────
:: Step 5: Start Backend (FastAPI on port 8001)
:: ─────────────────────────────────────────────────
echo [5/6] Starting FastAPI backend on port 8001...

:: Kill any existing process on port 8001
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8001 " ^| findstr "LISTENING" 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: Start backend in a new minimized window
start "ThreatVision Backend" /min cmd /c "cd /d "%~dp0backend" && .venv\Scripts\activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8001"

echo   [OK] Backend starting...
echo   Waiting for API health check...

:: Wait for backend to be healthy
set /a attempts=0
:healthcheck
set /a attempts+=1
if %attempts% gtr 30 (
    echo   [WARN] Backend health check timed out - it may still be starting.
    goto start_frontend
)
timeout /t 2 /nobreak >nul
curl -s http://127.0.0.1:8001/health >nul 2>&1
if %errorlevel% neq 0 goto healthcheck
echo   [OK] Backend is healthy!
echo.

:: ─────────────────────────────────────────────────
:: Step 6: Start Frontend (Next.js on port 3001)
:: ─────────────────────────────────────────────────
:start_frontend
echo [6/6] Starting Next.js frontend on port 3001...

:: Kill any existing process on port 3001
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3001 " ^| findstr "LISTENING" 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: Start frontend in a new minimized window
start "ThreatVision Frontend" /min cmd /c "cd /d "%~dp0frontend" && npm run dev -- -p 3001"

echo   [OK] Frontend starting on port 3001...
echo.

:: Wait a moment for Next.js to compile
timeout /t 8 /nobreak >nul

:: ─────────────────────────────────────────────────
:: Step 7: Register superadmin (if not exists)
:: ─────────────────────────────────────────────────
echo [BONUS] Registering superadmin user...
"backend\.venv\Scripts\python.exe" -c "import urllib.request,json,secrets,string;env={l.strip().split('=',1)[0]:l.strip().split('=',1)[1] for l in open('backend/.env') if '=' in l.strip() and not l.strip().startswith('#')};email=env.get('SUPERADMIN_EMAIL','admin@example.com');pw=''.join(secrets.choice(string.ascii_letters+string.digits) for _ in range(20))+'Aa1';req=urllib.request.Request('http://127.0.0.1:8001/auth/register',json.dumps({'email':email,'password':pw,'name':'Dev Admin'}).encode(),{'Content-Type':'application/json'});exec('try:\n r=urllib.request.urlopen(req,timeout=10);print(f\"  [OK] Registered: {email} / Password: {pw}\");open(\".dev_login_credentials.txt\",\"w\").write(f\"Email: {email}\\nPassword: {pw}\\nURL: http://127.0.0.1:3001/login\")\nexcept Exception as e:\n print(f\"  [INFO] User may already exist ({e}) - check .dev_login_credentials.txt\")')" 2>nul
echo.

:: ─────────────────────────────────────────────────
:: Open browser
:: ─────────────────────────────────────────────────
echo ══════════════════════════════════════════════════════════════
echo.
echo   ThreatVision is LIVE!
echo.
echo   Frontend:  http://127.0.0.1:3001
echo   Backend:   http://127.0.0.1:8001/health
echo   Login:     Check .dev_login_credentials.txt for credentials
echo.
echo   Press any key to open in browser...
echo.
echo ══════════════════════════════════════════════════════════════

pause >nul
start "" "http://127.0.0.1:3001"

echo.
echo   [!] Keep this window open. Close it to see shutdown instructions.
echo   [!] To stop services:
echo   [!]   - Close "ThreatVision Backend" and "ThreatVision Frontend" windows
echo   [!]   - Run: docker compose down (to stop Postgres)
echo.
pause
