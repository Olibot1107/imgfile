@echo off
echo 1: Run CLI
echo 2: Run GUI
echo 3: Install dependencies
echo 4 Exit
set /p choice=Enter your choice:
if "%choice%"=="1" (
    echo Starting CLI
    python3 cli.py
) else if "%choice%"=="2" (
    echo Starting GUI
    python3 gui.py
) else if "%choice%"=="3" (
    echo Installing dependencies
    pip install -r requirements.txt
) else if "%choice%"=="4" (
    echo Exiting
    exit
) else (
    echo Invalid choice. Please try again.
    pause
    start "" "%~f0"
)