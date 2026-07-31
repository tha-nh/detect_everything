@echo off
chcp 65001 > nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Chua cai dat. Hay chay setup_windows.bat truoc.
    pause
    exit /b 1
)

.venv\Scripts\python.exe gui.py
if errorlevel 1 pause
