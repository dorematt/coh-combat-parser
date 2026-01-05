@echo off
REM City of Heroes Combat Parser - Local Development Runner (Windows)
REM This script sets up a virtual environment and runs the parser

setlocal enabledelayedexpansion

set VENV_DIR=venv
set PYTHON_CMD=python

echo =================================================
echo   CoH Combat Parser - Local Development Runner
echo =================================================
echo.

REM Check if Python is installed
where %PYTHON_CMD% >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.12 or later from https://www.python.org/
    pause
    exit /b 1
)

REM Display Python version
for /f "tokens=*" %%i in ('%PYTHON_CMD% --version') do set PYTHON_VERSION=%%i
echo Using: %PYTHON_VERSION%
echo.

REM Create virtual environment if it doesn't exist
if not exist "%VENV_DIR%\" (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv %VENV_DIR%
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call %VENV_DIR%\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip -q

REM Install/update dependencies
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt -q

echo.
echo =================================================
echo   Starting CoH Combat Parser...
echo =================================================
echo.

REM Run the application
cd src
python CoH_Parser.py

REM Deactivate on exit
deactivate

pause
