@echo off
REM Development script to run Vogue Manager Desktop Application
REM Windows batch file

echo Starting Vogue Manager Desktop Application...

REM Change to project root directory
cd /d "%~dp0.."

REM Add src to Python path
set PYTHONPATH=%CD%\src;%PYTHONPATH%

REM Run the application
python -m vogue_app.main

pause
