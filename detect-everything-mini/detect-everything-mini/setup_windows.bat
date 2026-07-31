@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ==========================================
echo CAI DAT DETECT EVERYTHING MINI
echo ==========================================

where py >nul 2>nul
if %errorlevel%==0 (
    set PYTHON_CMD=py
) else (
    set PYTHON_CMD=python
)

%PYTHON_CMD% -m venv .venv
if errorlevel 1 (
    echo.
    echo Khong tao duoc moi truong Python.
    echo Hay cai Python 3.10 hoac 3.11 va chon Add Python to PATH.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Cai thu vien that bai. Hay kiem tra ket noi Internet.
    pause
    exit /b 1
)

echo.
echo CAI DAT HOAN TAT.
echo Chay run_gui.bat de mo chuong trinh.
pause
