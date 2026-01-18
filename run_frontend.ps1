# Run frontend locally (Windows PowerShell)
# Usage: Open PowerShell, run: .\run_frontend.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $scriptDir\frontend

if (-not (Test-Path node_modules)) {
    Write-Host "Installing frontend dependencies (npm install)..."
    npm install
}

Write-Host "Starting frontend dev server (vite)"
npm run dev -- --host 0.0.0.0 --port 5173

Pop-Location
