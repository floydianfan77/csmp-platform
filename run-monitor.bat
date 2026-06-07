@echo off
REM Launcher for CSMP monitor map + API. Double-click after running demo once.
setlocal
cd /d "%~dp0"

echo ---------------------------------------------------------------
echo  CSMP Monitor — map + API
echo  Map UI  : http://127.0.0.1:8000/app/
echo  API docs: http://127.0.0.1:8000/docs
echo.
echo  First time? Run demo.bat once to load sample data.
echo  (Close this window or press Ctrl+C to stop the server.)
echo ---------------------------------------------------------------

start "" http://127.0.0.1:8000/app/
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Makefile.ps1" monitor-api

echo.
echo Server stopped.
pause
