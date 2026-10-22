@echo off
title PhantomMirror OS - Launcher
color 0b

echo ====================================================
echo   PHANTOM_MIRROR OS v3.0 - LAUNCHING SYSTEM...
echo ====================================================
echo.

:: Go to the folder where this .bat file is located
cd /d "%~dp0"

:: Check if app.py is actually here
if not exist "app.py" (
    echo [X] ERROR: app.py not found!
    echo Please make sure you save this .bat file INSIDE the PhantomMirror folder.
    pause
    exit /b
)

:: Activate your Python virtual environment
if exist "venv\Scripts\activate.bat" (
    echo [*] Activating Virtual Environment...
    call venv\Scripts\activate.bat
) else (
    echo [!] Virtual environment not found. Using global Python.
)

:: Open the browser after a 3 second delay
echo [*] Opening Web Interface...
start "" cmd /c "timeout /t 3 >nul & start http://127.0.0.1:5000/"

:: Start the Flask server
echo [*] Starting Backend Server...
echo.
python app.py

:: Keep the window open if the server crashes
pause