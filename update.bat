@echo off
echo ==========================================
echo   PhotoBudka - Update
echo ==========================================
echo.
echo Downloading latest version from GitHub...

:: Download ZIP
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/YourJeisus/PhotoBudka/archive/refs/heads/master.zip' -OutFile '%TEMP%\photobudka.zip'"

if %errorlevel% neq 0 (
    echo [ERROR] Download failed. Check internet connection.
    pause
    exit /b 1
)

echo [OK] Downloaded

:: Extract, overwrite existing files
echo Extracting...
powershell -Command "Expand-Archive -Path '%TEMP%\photobudka.zip' -DestinationPath '%TEMP%\photobudka_update' -Force"

:: Copy files from extracted archive to current directory
echo Updating files...
xcopy "%TEMP%\photobudka_update\PhotoBudka-master\*" "%~dp0" /s /y /exclude:%~dp0photos\

:: Cleanup temp files
del "%TEMP%\photobudka.zip" 2>nul
rmdir /s /q "%TEMP%\photobudka_update" 2>nul

echo.
echo ==========================================
echo   Update complete!
echo   Run start.bat to launch
echo ==========================================
pause
