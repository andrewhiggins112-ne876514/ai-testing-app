@echo off
cd /d "%~dp0\.."
set "CURSOR_AGENT=%LOCALAPPDATA%\cursor-agent\agent.cmd"
if not exist "%CURSOR_AGENT%" (
  echo ERROR: Cursor agent not found at %CURSOR_AGENT%
  echo Install CLI first: irm https://cursor.com/install?win32=true ^| iex
  pause
  exit /b 1
)
echo Using: %CURSOR_AGENT%
echo Starting worker home-pc in %CD%
echo Leave this window open.
"%CURSOR_AGENT%" worker start --name "home-pc"
pause
