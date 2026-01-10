"""
Build script to create launcher.exe
Run this to compile launcher.py into a standalone executable
"""
import subprocess
import sys
from pathlib import Path

def main():
    print("=" * 50)
    print("  Building RustPlus Raid Alarms Launcher")
    print("=" * 50)
    print()
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✓ PyInstaller found")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("✓ PyInstaller installed")
    
    print()
    print("Building launcher.exe...")
    print("This may take a minute...")
    print()
    
    # Build the launcher
    result = subprocess.run([
        sys.executable,                 # Use current Python interpreter
        "-m", "PyInstaller",            # Run PyInstaller as module
        "--onefile",                    # Single executable
        "--console",                    # Keep console window visible
        "--name=RustPlusRaidAlarms",   # Output name
        "--icon=NONE",                  # Add icon if you have one
        "--clean",                      # Clean build
        "launcher.py"
    ])
    
    if result.returncode == 0:
        print()
        print("=" * 50)
        print("✓ Build successful!")
        print("=" * 50)
        print()
        print("Executable created at: dist\\RustPlusRaidAlarms.exe")
        print()
        print("You can now:")
        print("  1. Test it by running dist\\RustPlusRaidAlarms.exe")
        print("  2. Distribute it to users (they just double-click it)")
        print("  3. The .exe will auto-download Python if needed")
        print()
    else:
        print()
        print("=" * 50)
        print("❌ Build failed")
        print("=" * 50)
        sys.exit(1)

if __name__ == "__main__":
    main()
