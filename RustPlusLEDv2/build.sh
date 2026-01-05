#!/bin/bash
# Build script for RustPlusLEDv2
# Creates standalone executable for distribution

echo "🚀 Building Rust+ Multi-LED Trigger..."

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Error: Python not found. Please install Python 3.7+."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Install PyInstaller for building
echo "🔨 Installing PyInstaller..."
pip install pyinstaller

# Build the application
echo "🏗️ Building executable..."
pyinstaller --onefile \
    --windowed \
    --name "RustPlusLED" \
    --icon="assets/icon.ico" \
    --add-data "led_controllers.py;." \
    --hidden-import "led_controllers" \
    --hidden-import "PySide6.QtCore" \
    --hidden-import "PySide6.QtGui" \
    --hidden-import "PySide6.QtWidgets" \
    --hidden-import "telegram" \
    --hidden-import "telegram.ext" \
    main.py

# Check if build was successful
if [ -f "dist/RustPlusLED.exe" ] || [ -f "dist/RustPlusLED" ]; then
    echo "✅ Build successful!"
    echo "📁 Executable created in: dist/"
    echo "🎉 Ready for distribution!"
    
    # Create release directory structure
    echo "📦 Creating release package..."
    mkdir -p release
    cp -r dist/* release/
    cp README.md release/
    cp SETUP.md release/
    cp CONFIG_GUIDE.md release/
    cp requirements.txt release/
    
    echo "📦 Release package created in: release/"
else
    echo "❌ Build failed. Check errors above."
    exit 1
fi

echo "🎯 Build complete!"