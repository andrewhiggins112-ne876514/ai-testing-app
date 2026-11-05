# One-click: kill old Gradio on 7860, pull optional, start UI.
# Double-click or run:  powershell -ExecutionPolicy Bypass -File .\scripts\restart_ui.ps1

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "Repo: $PWD"

# Stop anything bound to 7860
Get-NetTCPConnection -LocalPort 7860 -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique |
  ForEach-Object {
    Write-Host "Stopping PID $_ on port 7860"
    Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
  }

Start-Sleep -Seconds 1

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
  Write-Host "ERROR: venv python not found. Create venv first." -ForegroundColor Red
  exit 1
}

if (-not (Select-String -Path ".\ui\gradio_app.py" -Pattern "Save preset" -Quiet)) {
  Write-Host "ERROR: ui\gradio_app.py has no Save preset — run git pull origin main first." -ForegroundColor Red
  exit 1
}

Write-Host "Starting UI (window stays open)..."
& .\venv\Scripts\python.exe .\run_ui.py
