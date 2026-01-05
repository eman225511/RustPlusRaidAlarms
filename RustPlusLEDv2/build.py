#!/usr/bin/env python3
"""
Cross-platform build script for RustPlusLEDv2
Creates standalone executable for distribution
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def run_command(command, shell=True):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=shell, check=True, 
                              capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def main():
    print("🚀 Building Rust+ Multi-LED Trigger...")
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7+ required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Check if virtual environment exists
    venv_path = Path(".venv")
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        success, output = run_command([sys.executable, "-m", "venv", ".venv"])
        if not success:
            print(f"❌ Failed to create virtual environment: {output}")
            sys.exit(1)
    
    # Determine activation script based on platform
    if platform.system() == "Windows":
        activate_script = venv_path / "Scripts" / "activate.bat"
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        activate_script = venv_path / "bin" / "activate"
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
    
    print("📥 Installing dependencies...")
    success, output = run_command([str(pip_exe), "install", "-r", "requirements.txt"])
    if not success:
        print(f"❌ Failed to install dependencies: {output}")
        sys.exit(1)
    
    print("🔨 Installing PyInstaller...")
    success, output = run_command([str(pip_exe), "install", "pyinstaller"])
    if not success:
        print(f"❌ Failed to install PyInstaller: {output}")
        sys.exit(1)
    
    # Build the application
    print("🏗️ Building executable...")
    
    # PyInstaller command
    pyinstaller_cmd = [
        str(venv_path / ("Scripts" if platform.system() == "Windows" else "bin") / "pyinstaller"),
        "--onefile",
        "--windowed",
        "--name", "RustPlusLED",
        "--add-data", f"led_controllers.py{os.pathsep}.",
        "--hidden-import", "led_controllers",
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtGui", 
        "--hidden-import", "PySide6.QtWidgets",
        "--hidden-import", "telegram",
        "--hidden-import", "telegram.ext",
        "main.py"
    ]
    
    # Add icon if it exists
    if Path("assets/icon.ico").exists():
        pyinstaller_cmd.extend(["--icon", "assets/icon.ico"])
    
    success, output = run_command(pyinstaller_cmd)
    if not success:
        print(f"❌ Build failed: {output}")
        sys.exit(1)
    
    # Check if executable was created
    exe_name = "RustPlusLED.exe" if platform.system() == "Windows" else "RustPlusLED"
    exe_path = Path("dist") / exe_name
    
    if exe_path.exists():
        print("✅ Build successful!")
        print(f"📁 Executable created: {exe_path}")
        
        # Create release package
        print("📦 Creating release package...")
        release_dir = Path("release")
        release_dir.mkdir(exist_ok=True)
        
        # Copy executable
        shutil.copy2(exe_path, release_dir / exe_name)
        
        # Copy documentation
        docs = ["README.md", "SETUP.md", "CONFIG_GUIDE.md", "requirements.txt"]
        for doc in docs:
            if Path(doc).exists():
                shutil.copy2(doc, release_dir / doc)
        
        print(f"📦 Release package created in: {release_dir}")
        print("🎉 Ready for distribution!")
        
        # Show file sizes
        exe_size = exe_path.stat().st_size / (1024 * 1024)
        print(f"📊 Executable size: {exe_size:.1f} MB")
        
    else:
        print("❌ Build failed - executable not found")
        sys.exit(1)
    
    print("🎯 Build complete!")

if __name__ == "__main__":
    main()