@echo off
setlocal enabledelayedexpansion

:: RustPlus Raid Alarms - Automatic Setup and Run Script
:: This script will check for Python, install it if needed, setup venv, and run the app

echo.
echo ========================================
echo  RustPlus Raid Alarms - Auto Setup
echo ========================================
echo.

:: Check if Python is installed
echo [1/5] Checking for Python installation...
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Python is installed
    set PYTHON_CMD=python
    goto :check_venv
)

:: Check if portable Python exists in the project folder
if exist "python-portable\python.exe" (
    echo [OK] Portable Python found
    set PYTHON_CMD=python-portable\python.exe
    goto :check_venv
)

:: Python not found - download portable version
echo [!] Python not found. Downloading portable Python 3.11...
echo.

:: Create temp directory for download
if not exist "temp" mkdir temp

:: Download Python embeddable package (portable)
echo Downloading Python 3.11.9 (64-bit portable)...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile 'temp\python.zip'}"

if %errorlevel% neq 0 (
    echo [ERROR] Failed to download Python. Please check your internet connection.
    pause
    exit /b 1
)

:: Extract Python
echo Extracting Python...
powershell -Command "Expand-Archive -Path 'temp\python.zip' -DestinationPath 'python-portable' -Force"

if %errorlevel% neq 0 (
    echo [ERROR] Failed to extract Python.
    pause
    exit /b 1
)

:: Download get-pip.py
echo Downloading pip installer...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'temp\get-pip.py'}"

:: Enable site-packages in portable Python
echo import site > python-portable\python311._pth.new
type python-portable\python311._pth >> python-portable\python311._pth.new
move /y python-portable\python311._pth.new python-portable\python311._pth >nul

:: Install pip in portable Python
echo Installing pip...
python-portable\python.exe temp\get-pip.py

:: Clean up temp files
rmdir /s /q temp 2>nul

echo [OK] Portable Python installed successfully
set PYTHON_CMD=python-portable\python.exe

:check_venv
:: Check if virtual environment exists
echo.
echo [2/5] Checking for virtual environment...
if exist ".venv\Scripts\python.exe" (
    echo [OK] Virtual environment found
    goto :install_deps
)

:: Create virtual environment
echo Creating virtual environment...
%PYTHON_CMD% -m venv .venv

if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    echo Trying to install venv module...
    %PYTHON_CMD% -m pip install virtualenv
    %PYTHON_CMD% -m virtualenv .venv
    
    if !errorlevel! neq 0 (
        echo [ERROR] Could not create virtual environment. Please install Python manually.
        pause
        exit /b 1
    )
)

echo [OK] Virtual environment created

:install_deps
:: Install/Update dependencies
echo.
echo [3/5] Installing dependencies...

:: Upgrade pip first
.venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1

:: Check if requirements.txt exists
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found!
    pause
    exit /b 1
)

:: Install requirements
.venv\Scripts\python.exe -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo [WARNING] Some dependencies may have failed to install.
    echo The application may still work, but some features might be unavailable.
    echo.
    pause
)

echo [OK] Dependencies installed

:: Check for config.json
echo.
echo [4/5] Checking configuration...
if exist "config.json" (
    echo [OK] Configuration file found
) else (
    echo [!] No config.json found - will be created on first run
)

:: Run the application
echo.
echo [5/5] Starting RustPlus Raid Alarms...
echo.
echo ========================================
echo.

.venv\Scripts\python.exe main.py

:: Keep window open if there was an error
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo [ERROR] Application exited with error code %errorlevel%
    echo ========================================
    pause
)

endlocal
