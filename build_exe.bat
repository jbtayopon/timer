@echo off
title Countdown Timer - EXE Builder
cd /d "%~dp0"

echo ==========================================
echo   Countdown Timer EXE Builder
echo ==========================================
echo.

if not exist "countdown.py" (
    echo ERROR: countdown.py was not found.
    echo Put this BAT file in the same folder as countdown.py.
    pause
    exit /b 1
)

echo [1/3] Installing/updating required packages...
python -m pip install --upgrade PySide6 PyInstaller
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install requirements.
    pause
    exit /b 1
)

echo.
echo [2/3] Cleaning previous build...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "Countdown.spec" del /q "Countdown.spec"

echo.
echo [3/3] Building Countdown.exe...
python -m PyInstaller --noconfirm --clean --windowed --onefile --name "Countdown" "countdown.py"

if errorlevel 1 (
    echo.
    echo BUILD FAILED.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   BUILD SUCCESSFUL
echo ==========================================
echo.
echo EXE:
echo %cd%\dist\Countdown.exe
echo.
pause
