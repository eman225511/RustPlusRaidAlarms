"""
RustPlus Raid Alarms - Automatic Setup and Launcher
This will check for Python, install it if needed, setup venv, and run the app
"""
import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil
from pathlib import Path

def print_header(text):
    """Print a formatted header"""
    print()
    print("=" * 50)
    print(f"  {text}")
    print("=" * 50)
    print()

def print_step(step, total, message):
    """Print a step message"""
    print(f"[{step}/{total}] {message}")

def check_python():
    """Check if Python is available, return path to python executable"""
    script_dir = Path(__file__).parent
    
    print_step(1, 5, "Checking for Python installation...")
    
    # Check if python command works
    try:
        result = subprocess.run(
            ["python", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print("[OK] Python is installed:", result.stdout.strip())
        return "python"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Check for portable Python in project folder
    portable_python = script_dir / "python-portable" / "python.exe"
    if portable_python.exists():
        print("[OK] Portable Python found")
        return str(portable_python)
    
    # Python not found - download portable version
    print("[!] Python not found. Downloading portable Python 3.11...")
    return download_portable_python(script_dir)

def download_portable_python(script_dir):
    """Download and setup portable Python"""
    temp_dir = script_dir / "temp"
    portable_dir = script_dir / "python-portable"
    
    try:
        # Create temp directory
        temp_dir.mkdir(exist_ok=True)
        
        # Download Python embeddable package
        python_url = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
        python_zip = temp_dir / "python.zip"
        
        print("Downloading Python 3.11.9 (64-bit portable)...")
        print("This may take a few minutes...")
        
        urllib.request.urlretrieve(python_url, python_zip)
        print("[OK] Download complete")
        
        # Extract Python
        print("Extracting Python...")
        portable_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(python_zip, 'r') as zip_ref:
            zip_ref.extractall(portable_dir)
        print("[OK] Python extracted")
        
        # Download get-pip.py
        print("Downloading pip installer...")
        pip_url = "https://bootstrap.pypa.io/get-pip.py"
        get_pip = temp_dir / "get-pip.py"
        urllib.request.urlretrieve(pip_url, get_pip)
        
        # Enable site-packages in portable Python
        pth_file = portable_dir / "python311._pth"
        if pth_file.exists():
            content = pth_file.read_text()
            if "import site" not in content:
                pth_file.write_text("import site\n" + content)
        
        # Install pip in portable Python
        print("Installing pip...")
        python_exe = portable_dir / "python.exe"
        subprocess.run([str(python_exe), str(get_pip)], check=True, capture_output=True)
        print("[OK] Pip installed")
        
        # Clean up temp files
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        print("[OK] Portable Python installed successfully")
        return str(python_exe)
        
    except Exception as e:
        print(f"[ERROR] Failed to download/install Python: {e}")
        print()
        print("Please install Python manually from: https://www.python.org/downloads/")
        print("Make sure to check 'Add Python to PATH' during installation")
        input("\nPress Enter to exit...")
        sys.exit(1)

def setup_venv(python_cmd, script_dir):
    """Setup virtual environment"""
    print_step(2, 5, "Checking for virtual environment...")
    
    venv_python = script_dir / ".venv" / "Scripts" / "python.exe"
    
    if venv_python.exists():
        print("[OK] Virtual environment found")
        return venv_python
    
    # Create virtual environment
    print("Creating virtual environment...")
    try:
        subprocess.run([python_cmd, "-m", "venv", ".venv"], check=True, cwd=script_dir)
        print("[OK] Virtual environment created")
        return venv_python
    except subprocess.CalledProcessError:
        # Try with virtualenv module
        print("Trying alternate method...")
        try:
            subprocess.run([python_cmd, "-m", "pip", "install", "virtualenv"], check=True)
            subprocess.run([python_cmd, "-m", "virtualenv", ".venv"], check=True, cwd=script_dir)
            print("[OK] Virtual environment created")
            return venv_python
        except Exception as e:
            print(f"[ERROR] Failed to create virtual environment: {e}")
            print("Please install Python with venv support")
            input("\nPress Enter to exit...")
            sys.exit(1)

def install_dependencies(venv_python, script_dir):
    """Install dependencies from requirements.txt"""
    print_step(3, 5, "Installing dependencies...")
    
    # Upgrade pip first
    print("Upgrading pip...")
    try:
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            check=True
        )
    except:
        pass  # Non-critical if pip upgrade fails
    
    # Check for requirements.txt
    requirements_file = script_dir / "requirements.txt"
    if not requirements_file.exists():
        print("[ERROR] requirements.txt not found!")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Install requirements
    print("Installing required packages...")
    print("This may take a few minutes on first run...")
    try:
        result = subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=script_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("[WARNING] Some dependencies may have failed to install")
            print("The application may still work, but some features might be unavailable")
            print()
            print("Error output:")
            print(result.stderr)
            input("\nPress any key to continue...")
        else:
            print("[OK] Dependencies installed")
    except Exception as e:
        print(f"[WARNING] Error installing dependencies: {e}")
        print("The application may still work, but some features might be unavailable")
        input("\nPress any key to continue...")

def check_config(script_dir):
    """Check for config file"""
    print_step(4, 5, "Checking configuration...")
    
    config_file = script_dir / "config.json"
    if config_file.exists():
        print("[OK] Configuration file found")
    else:
        print("[!] No config.json found - will be created on first run")

def run_application(venv_python, script_dir):
    """Run the main application"""
    print_step(5, 5, "Starting RustPlus Raid Alarms...")
    print()
    print("=" * 50)
    print()
    
    main_py = script_dir / "main.py"
    
    try:
        result = subprocess.run([str(venv_python), str(main_py)], cwd=script_dir)
        
        if result.returncode != 0:
            print()
            print("=" * 50)
            print(f"[ERROR] Application exited with error code {result.returncode}")
            print("=" * 50)
            input("\nPress Enter to exit...")
            sys.exit(result.returncode)
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print()
        print("=" * 50)
        print(f"[ERROR] Failed to start application: {e}")
        print("=" * 50)
        input("\nPress Enter to exit...")
        sys.exit(1)

def main():
    """Main launcher function"""
    # Get script directory (handle both script and frozen exe)
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        script_dir = Path(sys.executable).parent
    else:
        # Running as script
        script_dir = Path(__file__).parent
    
    os.chdir(script_dir)
    
    print_header("RustPlus Raid Alarms - Auto Setup/Run")
    
    try:
        # Step 1: Check for Python
        python_cmd = check_python()
        
        # Step 2: Setup virtual environment
        venv_python = setup_venv(python_cmd, script_dir)
        
        # Step 3: Install dependencies
        install_dependencies(venv_python, script_dir)
        
        # Step 4: Check config
        check_config(script_dir)
        
        # Step 5: Run the application
        run_application(venv_python, script_dir)
        
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print()
        print("=" * 50)
        print(f"[ERROR] Unexpected error: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
