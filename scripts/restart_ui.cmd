@echo off
cd /d "%~dp0\.."
echo Repo: %CD%

for /f "tokens=5" %%p in ('netstat -ano ^| findstr :7860 ^| findstr LISTENING') do (
  echo Stopping PID %%p on port 7860
  taskkill /F /PID %%p >nul 2>&1
)

if not exist "venv\Scripts\python.exe" (
  echo ERROR: venv python not found.
  exit /b 1
)

echo Starting UI...
"venv\Scripts\python.exe" "run_ui.py"
pause
