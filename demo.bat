@echo off
REM Load sample data: broker + producer + aggregate + warehouse.
setlocal
cd /d "%~dp0"

echo ---------------------------------------------------------------
echo  CSMP demo — loading sample traffic data
echo  This starts Redpanda, publishes events, and builds csmp.duckdb
echo ---------------------------------------------------------------

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Makefile.ps1" demo

echo.
echo Done. Double-click run-monitor.bat to open the map.
pause
