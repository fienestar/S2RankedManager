"""Build SpelunkyRankedManager.exe with PyInstaller."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"


def ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def build() -> None:
    ensure_pyinstaller()
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")])

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        "SpelunkyRankedManager",
        "--onefile",
        "--windowed",
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
        "--specpath",
        str(BUILD_DIR),
        "--clean",
        "--noconfirm",
        str(ROOT / "app.py"),
    ]
    subprocess.check_call(cmd)


if __name__ == "__main__":
    build()

