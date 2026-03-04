@echo off
echo ==========================================
echo   PhotoBudka - Install
echo ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Download from https://www.python.org/downloads/
    echo Check "Add Python to PATH" during install
    pause
    exit /b 1
)

echo [OK] Python found
python --version

:: Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

:: Create photos directory
if not exist "photos" mkdir photos

echo.
echo ==========================================
echo   Install complete!
echo   Run start.bat to launch
echo ==========================================
pause
