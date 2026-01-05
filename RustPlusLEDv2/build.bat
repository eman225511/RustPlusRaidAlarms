@echo off
REM Build script for RustPlusLEDv2 (Windows)
REM Creates standalone executable for distribution

echo 🚀 Building Rust+ Multi-LED Trigger...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python not found. Please install Python 3.7+.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo ⚡ Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Install PyInstaller for building
echo 🔨 Installing PyInstaller...
pip install pyinstaller

REM Build the application
echo 🏗️ Building executable...
pyinstaller --onefile ^
    --windowed ^
    --name "RustPlusLED" ^
    --icon="assets\icon.ico" ^
    --add-data "led_controllers.py;." ^
    --hidden-import "led_controllers" ^
    --hidden-import "PySide6.QtCore" ^
    --hidden-import "PySide6.QtGui" ^
    --hidden-import "PySide6.QtWidgets" ^
    --hidden-import "telegram" ^
    --hidden-import "telegram.ext" ^
    main.py

REM Check if build was successful
if exist "dist\RustPlusLED.exe" (
    echo ✅ Build successful!
    echo 📁 Executable created in: dist\
    echo 🎉 Ready for distribution!
    
    REM Create release directory structure
    echo 📦 Creating release package...
    if not exist "release" mkdir release
    xcopy /Y dist\*.* release\
    copy README.md release\
    copy SETUP.md release\
    copy CONFIG_GUIDE.md release\
    copy requirements.txt release\
    
    echo 📦 Release package created in: release\
) else (
    echo ❌ Build failed. Check errors above.
    pause
    exit /b 1
)

echo 🎯 Build complete!
pause