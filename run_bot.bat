@echo off
REM Turd News Network Enhanced - Windows Startup Script
title Turd News Network Enhanced v4.0

REM Enable ANSI colors in Windows Command Prompt
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do (
  set ESC=%%b
)

cls
echo ===============================================================================
echo                    WSB MONITOR ENHANCED v4.0
echo                  Reddit DD Tracker with AI Analysis
echo ===============================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

REM Run the bot
echo [*] Starting bot...
echo.
python -W ignore main.py --single

echo.
echo ===============================================================================
echo                         Bot execution completed
echo ===============================================================================
pause
