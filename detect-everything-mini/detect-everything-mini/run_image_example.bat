@echo off
chcp 65001 > nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Chua cai dat. Hay chay setup_windows.bat truoc.
    pause
    exit /b 1
)

if not exist "input\test.jpg" (
    echo Hay dat anh vao input\test.jpg truoc.
    pause
    exit /b 1
)

.venv\Scripts\python.exe app.py ^
  --source "input\test.jpg" ^
  --classes "person,laptop,mobile phone,bottle" ^
  --confidence 0.25

pause
