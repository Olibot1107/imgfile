@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:: Check if an argument was provided
IF "%~1"=="" (
    echo No arguments provided. Please choose an option:
    echo 1: Run CLI
    echo 2: Run GUI
    echo 3: Install dependencies
    echo 4: Exit
    set /p choice="Enter your choice (1-4): "
) ELSE (
    set choice=%~1
)

:: Process choice
IF "%choice%"=="1" (
    echo Starting CLI...
    python cli.py
    goto :eof
)

IF "%choice%"=="2" (
    echo Starting GUI...
    python app.py
    goto :eof
)

IF "%choice%"=="3" (
    echo Installing dependencies...
    pip install -r requirements.txt
    goto :eof
)

IF "%choice%"=="4" (
    echo Exiting...
    exit /b 0
)

:: If none of the above
echo Invalid choice. Please run the script again and choose a valid option.
exit /b 1
