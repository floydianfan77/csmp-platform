@echo off
REM Load sample data: broker + producer + aggregate + warehouse.
setlocal
cd /d "%~dp0"

echo ---------------------------------------------------------------
echo  CSMP demo — OpenStreetMap seed + sample traffic data
echo  Downloads ~195 traffic signals for Chapeco, then publishes telemetry.
echo ---------------------------------------------------------------

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Makefile.ps1" demo

echo.
echo Done. Double-click run-monitor.bat to open the map.
pause
