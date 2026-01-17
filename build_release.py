import subprocess
import shutil
from pathlib import Path
import sys

RELEASE_DIR = Path("release").resolve()
DIST_EXE = Path("dist") / "RustPlusRaidAlarms.exe"
ROOT = Path(__file__).parent.resolve()

# Files we always bundle (core app + launcher helpers)
ROOT_FILES = [
    "main.py",
    "plugin_base.py",
    "relay_server.py",
    "telegram_service.py",
    "fcm_service.py",
    "requirements.txt",
    "run.bat",
]


def run_build_launcher():
    print("[1/3] Building launcher exe via PyInstaller...")
    subprocess.check_call([sys.executable, "build_launcher.py"], cwd=ROOT)
    if not DIST_EXE.exists():
        raise FileNotFoundError(f"Launcher exe not found at {DIST_EXE}")
    print(f"    ✓ Built {DIST_EXE}")


def prepare_release_dir():
    if RELEASE_DIR.exists():
        shutil.rmtree(RELEASE_DIR)
    RELEASE_DIR.mkdir(parents=True)
    (RELEASE_DIR / "plugins").mkdir(parents=True, exist_ok=True)  # empty; store will download plugins
    print(f"[2/3] Prepared release directory at {RELEASE_DIR}")


def copy_files():
    print("[3/3] Copying files...")
    # Copy exe
    shutil.copy2(DIST_EXE, RELEASE_DIR / DIST_EXE.name)

    # Copy root files if they exist
    for name in ROOT_FILES:
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, RELEASE_DIR / src.name)
        else:
            print(f"    ⚠ Skipping missing file: {src}")



    # Copy scripts folder
    scripts_src = ROOT / "scripts"
    scripts_dst = RELEASE_DIR / "scripts"
    if scripts_src.exists():
        shutil.copytree(scripts_src, scripts_dst, dirs_exist_ok=True)
    else:
        print(f"    ⚠ Skipping missing folder: {scripts_src}")

    print("    ✓ Copy complete")


def main():
    run_build_launcher()
    prepare_release_dir()
    copy_files()
    print("Release bundle ready in ./release")


if __name__ == "__main__":
    main()
