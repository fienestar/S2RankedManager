"""Configuration constants for Spelunky Ranked Manager."""

from __future__ import annotations

import os
import sys
import json
from pathlib import Path

APP_NAME = "S2Ranked Manager"
APP_VERSION = "0.1.0"
MANAGER_EXE_NAME = "SpelunkyRankedManager.exe"

MANAGER_OWNER = "fienestar"
MANAGER_REPO = "S2RankedManager"
MANAGER_REPO_URL = f"https://github.com/{MANAGER_OWNER}/{MANAGER_REPO}"
MANAGER_LATEST_RELEASE_API = (
    f"https://api.github.com/repos/{MANAGER_OWNER}/{MANAGER_REPO}/releases/latest"
)

RANKED_OWNER = "ZSRoach"
RANKED_REPO = "SpelunkyRanked"
RELEASES_URL = f"https://github.com/{RANKED_OWNER}/{RANKED_REPO}/releases"
LATEST_RELEASE_API = (
    f"https://api.github.com/repos/{RANKED_OWNER}/{RANKED_REPO}/releases/latest"
)

S2RANKED_ZIP_NAME = "S2Ranked.zip"
SPELUNKY_RANKED_ZIP_NAME = "SpelunkyRanked.zip"

MODLUNKY_CONFIG_RELATIVE = Path("spelunky.fyi") / "modlunky2" / "config.json"
MODLUNKY_INSTALL_DIR_KEY = "install-dir"

MANAGER_SETTINGS_FILE = "manager_config.json"
MANAGER_LOG_FILE = "manager_log"
PERSISTENT_S2RANKED_FILES = {
    MANAGER_EXE_NAME,
    MANAGER_SETTINGS_FILE,
    MANAGER_LOG_FILE,
    "settings.json",
}


def runtime_dir() -> Path:
    """Return runtime directory containing script or frozen executable."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def manager_settings_path() -> Path:
    return manager_data_dir() / MANAGER_SETTINGS_FILE


def log_path() -> Path:
    return manager_data_dir() / MANAGER_LOG_FILE


def local_app_data_dir() -> Path:
    raw = os.environ.get("LOCALAPPDATA", "").strip()
    if not raw:
        raise RuntimeError("LOCALAPPDATA is not set.")
    return Path(raw).resolve()


def modlunky_config_path() -> Path:
    return local_app_data_dir() / MODLUNKY_CONFIG_RELATIVE


def manager_data_dir() -> Path:
    """Return persistent manager data dir under {install-dir}/S2Ranked."""
    try:
        cfg_path = modlunky_config_path()
        if cfg_path.exists():
            with cfg_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            install_dir = payload.get(MODLUNKY_INSTALL_DIR_KEY, "")
            if isinstance(install_dir, str) and install_dir.strip():
                return Path(install_dir).expanduser().resolve() / "S2Ranked"
    except Exception:
        pass
    return Path.cwd().resolve() / "S2Ranked"
