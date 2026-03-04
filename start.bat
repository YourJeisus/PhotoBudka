@echo off
echo ==========================================
echo   PhotoBudka - Starting
echo ==========================================

:: Start Flask server in background
start "PhotoBudka Server" /min python app.py

:: Wait for server to start
echo Starting server...
timeout /t 3 /nobreak >nul

:: Open Chrome in kiosk mode
echo Opening browser...

set CHROME_PATH=
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
)
if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
)

if defined CHROME_PATH (
    start "" "%CHROME_PATH%" --kiosk --disable-infobars --no-first-run http://localhost:8080
) else (
    echo Chrome not found, opening default browser...
    start http://localhost:8080
)

echo.
echo App running at http://localhost:8080
echo Close this window to stop the server
