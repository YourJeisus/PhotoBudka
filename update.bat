@echo off
echo ==========================================
echo   PhotoBudka - Update
echo ==========================================
echo.
echo Downloading latest version from GitHub...

:: Download ZIP
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/YourJeisus/PhotoBudka/archive/refs/heads/master.zip' -OutFile '%TEMP%\photobudka.zip'"

if not exist "%TEMP%\photobudka.zip" goto :download_failed

echo [OK] Downloaded

:: Clean previous extract
if exist "%TEMP%\photobudka_update" rmdir /s /q "%TEMP%\photobudka_update"

:: Extract
echo Extracting...
powershell -Command "Expand-Archive -Path '%TEMP%\photobudka.zip' -DestinationPath '%TEMP%\photobudka_update' -Force"

:: Copy all files and folders preserving structure
echo Updating files...
set "SRC=%TEMP%\photobudka_update\PhotoBudka-master"
set "DST=%~dp0"

:: Copy root files
copy /y "%SRC%\*.py" "%DST%" >nul 2>&1
copy /y "%SRC%\*.txt" "%DST%" >nul 2>&1
copy /y "%SRC%\*.bat" "%DST%" >nul 2>&1
copy /y "%SRC%\.git*" "%DST%" >nul 2>&1

:: Copy static folder
if not exist "%DST%static" mkdir "%DST%static"
copy /y "%SRC%\static\*" "%DST%static\" >nul 2>&1

:: Copy templates folder
if not exist "%DST%templates" mkdir "%DST%templates"
copy /y "%SRC%\templates\*" "%DST%templates\" >nul 2>&1

:: Cleanup temp files
del "%TEMP%\photobudka.zip" 2>nul
rmdir /s /q "%TEMP%\photobudka_update" 2>nul

echo.
echo ==========================================
echo   Update complete!
echo   Run start.bat to launch
echo ==========================================
pause
goto :eof

:download_failed
echo [ERROR] Download failed. Check internet connection.
pause
goto :eof
