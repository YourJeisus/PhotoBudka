@echo off
echo ==========================================
echo   PhotoBudka - Install
echo ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Downloading and installing...
    echo This may take a few minutes...
    echo.

    :: Download Python installer
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"

    if not exist "%TEMP%\python_installer.exe" (
        echo [ERROR] Failed to download Python. Check internet connection.
        pause
        exit /b 1
    )

    :: Silent install with PATH
    echo Installing Python (silent)...
    "%TEMP%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1

    :: Cleanup installer
    del "%TEMP%\python_installer.exe" 2>nul

    :: Refresh PATH in current session
    set "PATH=%PATH%;C:\Program Files\Python312;C:\Program Files\Python312\Scripts"

    :: Verify
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python install failed. Try installing manually:
        echo https://www.python.org/downloads/
        echo Check "Add Python to PATH" during install
        pause
        exit /b 1
    )
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
