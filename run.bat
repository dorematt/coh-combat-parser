@echo off
REM City of Heroes Combat Parser - Local Development Runner (Windows)
REM This script sets up a virtual environment and runs the parser

setlocal enabledelayedexpansion

set VENV_DIR=venv
set PYTHON_CMD=
set PYTHON_VERSION=

echo =================================================
echo   CoH Combat Parser - Local Development Runner
echo =================================================
echo.

REM Try to find Python 3.12 in order of preference
echo Searching for Python 3.12...

REM 1. Try Python Launcher with -3.12 flag (works with multiple Python versions)
py -3.12 --version >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=py -3.12
    for /f "tokens=2" %%i in ('py -3.12 --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo Found Python 3.12 via Python Launcher
    goto :found_python
)

REM 2. Try python3.12 command
python3.12 --version >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=python3.12
    for /f "tokens=2" %%i in ('python3.12 --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo Found python3.12
    goto :found_python
)

REM 3. Try python312 command
python312 --version >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=python312
    for /f "tokens=2" %%i in ('python312 --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo Found python312
    goto :found_python
)

REM 4. Fall back to default python command
python --version >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=python
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo Found python
    goto :found_python
)

REM No Python found at all
echo ERROR: Python is not installed or not in PATH
echo Please install Python 3.12 from https://www.python.org/
echo.
echo TIP: The Python installer includes a "Python Launcher" that helps manage multiple versions
pause
exit /b 1

:found_python
echo Using: Python %PYTHON_VERSION%

REM Extract major and minor version (e.g., 3.12 from 3.12.1)
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR_VERSION=%%a
    set MINOR_VERSION=%%b
)

REM Check if version is 3.12
if not "%MAJOR_VERSION%"=="3" goto :version_warning
if not "%MINOR_VERSION%"=="12" goto :version_warning
goto :version_ok

:version_warning
echo.
echo WARNING: Python 3.12 is required for this project.
echo You are using Python %PYTHON_VERSION% which may not be compatible.
echo PyQt5 and other dependencies may fail to install on Python 3.13+.
echo.
echo Please install Python 3.12 from https://www.python.org/
echo.
set /p CONTINUE="Continue anyway? (y/N): "
if /i not "%CONTINUE%"=="y" (
    exit /b 1
)

:version_ok
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

