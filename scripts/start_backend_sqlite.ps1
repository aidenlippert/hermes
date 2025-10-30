# Starts Hermes backend with SQLite fallback (Windows PowerShell)
# Usage: Right-click -> Run with PowerShell, or run from a PS prompt.

$ErrorActionPreference = 'Stop'

$workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $workspace
Set-Location $repoRoot

# Configure SQLite file in repo root
$env:DATABASE_URL = "sqlite+aiosqlite:///$repoRoot/hermes_dev.db"
$env:PYTHONUNBUFFERED = '1'
# Prefer a passwordless local Redis by default (override with REDIS_URL if needed)
if (-not $env:REDIS_URL) {
	$env:REDIS_URL = 'redis://localhost:6379/0'
}

Write-Host "DATABASE_URL set to $env:DATABASE_URL" -ForegroundColor Cyan
Write-Host "REDIS_URL set to $env:REDIS_URL" -ForegroundColor Cyan
Write-Host "Starting Hermes backend on http://127.0.0.1:8000 ..." -ForegroundColor Green

python -m uvicorn backend.main_v2:app --host 127.0.0.1 --port 8000 --log-level info
