@echo off
chcp 65001 >nul
echo ==========================================
echo   PhotoBudka — Запуск
echo ==========================================

:: Start Flask server in background
start "PhotoBudka Server" /min python app.py

:: Wait for server to start
echo Запуск сервера...
timeout /t 3 /nobreak >nul

:: Open Chrome in kiosk mode
echo Открываю браузер...

:: Try common Chrome paths
set CHROME_PATH=
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
)
if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
)

if defined CHROME_PATH (
    start "" "%CHROME_PATH%" --kiosk --disable-infobars --no-first-run http://localhost:5000
) else (
    echo Chrome не найден, открываю в браузере по умолчанию...
    start http://localhost:5000
)

echo.
echo Приложение запущено на http://localhost:5000
echo Закройте это окно чтобы остановить сервер
