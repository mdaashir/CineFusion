@echo off
REM CineFusion Development Setup and Server Launcher
REM Windows Batch Script

echo.
echo ========================================
echo   CineFusion Development Server
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Display Python version
echo Checking Python installation...
python --version

REM Check if we're in the right directory
if not exist "package.json" (
    if not exist "Frontend" (
        echo Error: This script must be run from the CineFusion project root directory
        echo Make sure you have Frontend folder and package.json in the current directory
        pause
        exit /b 1
    )
)

echo.
echo Starting CineFusion development server...
echo.
echo Tips:
echo - Press Ctrl+C to stop the server
echo - The browser will open automatically
echo - Server will run on http://localhost:8000
echo.

REM Start the development server
python dev_server.py

echo.
echo Server has stopped. Press any key to exit...
pause >nul
