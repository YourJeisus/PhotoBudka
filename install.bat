@echo off
chcp 65001 >nul
echo ==========================================
echo   PhotoBudka — Установка
echo ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не найден!
    echo Скачайте Python с https://www.python.org/downloads/
    echo При установке отметьте "Add Python to PATH"
    pause
    exit /b 1
)

echo [OK] Python найден
python --version

:: Install dependencies
echo.
echo Устанавливаю зависимости...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo [ОШИБКА] Не удалось установить зависимости
    pause
    exit /b 1
)

:: Create photos directory
if not exist "photos" mkdir photos

echo.
echo ==========================================
echo   Установка завершена!
echo   Запустите start.bat для старта
echo ==========================================
pause
