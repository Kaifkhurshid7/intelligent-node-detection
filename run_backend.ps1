# Run backend locally (Windows PowerShell)
# Usage: Open PowerShell, run: .\run_backend.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $scriptDir\backend

if (-not (Test-Path .venv)) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

# Use the venv's python to install requirements and run uvicorn
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m spacy download en_core_web_sm

Write-Host "Starting backend (uvicorn) on http://0.0.0.0:8000"
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000

Pop-Location
