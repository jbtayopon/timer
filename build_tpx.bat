@echo off
setlocal

title TPX - Timer Pro X EXE Builder

cd /d "%~dp0"

echo ==========================================
echo        TPX - Timer Pro X
echo        EXE BUILDER
echo ==========================================
echo.

if not exist "countdown.py" (
    echo ERROR: countdown.py was not found.
    echo Put this BAT file in the same folder as countdown.py.
    echo.
    pause
    exit /b 1
)

if not exist "assets" (
    echo ERROR: assets folder was not found.
    echo Make sure the assets folder is beside countdown.py.
    echo.
    pause
    exit /b 1
)

if not exist "assets\splash.png" (
    echo ERROR: assets\splash.png was not found.
    echo.
    pause
    exit /b 1
)

if not exist "assets\tpx-icon.png" (
    echo ERROR: assets\tpx-icon.png was not found.
    echo.
    pause
    exit /b 1
)

echo [1/4] Installing/updating required packages...
echo.

python -m pip install --upgrade PySide6 PyInstaller

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install requirements.
    pause
    exit /b 1
)

echo.
echo [2/4] Cleaning previous build...
echo.

if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "TPX.spec" del /q "TPX.spec"

echo.
echo [3/4] Building TPX.exe...
echo.

python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --onefile ^
    --name "TPX" ^
    --add-data "assets;assets" ^
    --icon "assets\tpx-icon.png" ^
    "countdown.py"

if errorlevel 1 (
    echo.
    echo ==========================================
    echo              BUILD FAILED
    echo ==========================================
    echo.
    pause
    exit /b 1
)

echo.
echo [4/4] Finalizing...
echo.

echo ==========================================
echo           BUILD SUCCESSFUL
echo ==========================================
echo.
echo Application:
echo %cd%\dist\TPX.exe
echo.
echo Assets included:
echo   - TPX Icon
echo   - TPX Splash Screen
echo.
echo ==========================================
echo.

pause
endlocal