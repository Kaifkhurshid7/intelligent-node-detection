# Launch backend and frontend in separate PowerShell windows (Windows)
# Usage: Start-Process powershell -ArgumentList '-NoExit','-ExecutionPolicy','Bypass','-File','"$PSScriptRoot\\run_backend.ps1"'
#        Start-Process powershell -ArgumentList '-NoExit','-ExecutionPolicy','Bypass','-File','"$PSScriptRoot\\run_frontend.ps1"'

Write-Host "Launching backend in a new PowerShell window..."
Start-Process powershell -ArgumentList '-NoExit','-ExecutionPolicy','Bypass','-File',"$PSScriptRoot\run_backend.ps1"

Start-Sleep -Seconds 2

Write-Host "Launching frontend in a new PowerShell window..."
Start-Process powershell -ArgumentList '-NoExit','-ExecutionPolicy','Bypass','-File',"$PSScriptRoot\run_frontend.ps1"

Write-Host "Both processes started. Check the new windows for logs."
