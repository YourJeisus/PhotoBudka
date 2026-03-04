@echo off
echo ==========================================
echo   PhotoBudka - Install
echo ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% equ 0 goto :python_ok

echo Python not found. Downloading and installing...
echo This may take a few minutes...
echo.

:: Download Python installer
echo Downloading Python 3.12...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"

if not exist "%TEMP%\python_installer.exe" goto :download_failed

echo [OK] Python downloaded
echo Installing Python - a setup window will open...
echo Close the setup window when installation is done.
"%TEMP%\python_installer.exe" InstallAllUsers=1 PrependPath=1 Include_pip=1

del "%TEMP%\python_installer.exe" 2>nul

:: Refresh PATH
set "PATH=%PATH%;C:\Program Files\Python312;C:\Program Files\Python312\Scripts"

python --version >nul 2>&1
if %errorlevel% neq 0 goto :install_failed

:python_ok
echo [OK] Python found:
python --version
echo.

:: Install dependencies
echo Installing Python packages...
pip install -r requirements.txt
echo.

:: Create photos directory
if not exist "photos" mkdir photos

echo ==========================================
echo   Install complete!
echo   Run start.bat to launch
echo ==========================================
echo.
pause
goto :eof

:download_failed
echo [ERROR] Failed to download Python. Check internet connection.
pause
goto :eof

:install_failed
echo [ERROR] Python install failed.
echo Try installing manually from https://www.python.org/downloads/
echo IMPORTANT: Check "Add Python to PATH" during install!
pause
goto :eof
