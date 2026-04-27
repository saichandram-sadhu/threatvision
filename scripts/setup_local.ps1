# ThreatVision one-shot local setup (Windows PowerShell).
# Prerequisite: Docker Desktop running (for Postgres on port 55432).

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> Generating backend/.env + frontend/.env.local (SUPERADMIN_EMAIL from .env.example)"
& "$Root\backend\.venv\Scripts\python.exe" "$Root\scripts\bootstrap_env.py"

Write-Host "==> Starting Postgres (docker compose)"
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Docker failed. Start Docker Desktop, then run:" -ForegroundColor Yellow
    Write-Host "  cd $Root" -ForegroundColor Yellow
    Write-Host "  docker compose up -d" -ForegroundColor Yellow
    Write-Host "  backend\.venv\Scripts\python.exe backend\scripts\apply_migrations.py" -ForegroundColor Yellow
    exit 1
}

Write-Host "==> Waiting for Postgres..."
Start-Sleep -Seconds 8

Write-Host "==> Applying SQL migrations"
& "$Root\backend\.venv\Scripts\python.exe" "$Root\backend\scripts\apply_migrations.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Platform MISP (Docker auto — ok if MISP stack not running)"
& "$Root\backend\.venv\Scripts\python.exe" "$Root\backend\scripts\set_platform_misp_from_env.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  (MISP sync skipped or failed — start MISP Docker and re-run the script above.)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Done. Next:" -ForegroundColor Green
Write-Host "  Terminal 1: cd $Root\backend; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 127.0.0.1 --port 8001"
Write-Host "  Terminal 2: cd $Root\frontend; npm run dev"
Write-Host "  Browser: http://localhost:3000/register  (use the SUPERADMIN_EMAIL from .env.example, then login)"
