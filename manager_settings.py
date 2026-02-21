"""Persistent manager settings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import manager_settings_path


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        return data if isinstance(data, dict) else {}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_settings() -> dict[str, Any]:
    return _read_json(manager_settings_path())


def save_settings(data: dict[str, Any]) -> None:
    _write_json(manager_settings_path(), data)


def get_installed_version() -> str:
    settings = load_settings()
    value = settings.get("installed_version", "")
    return str(value) if value else ""


def set_installed_version(version: str) -> None:
    settings = load_settings()
    settings["installed_version"] = version
    save_settings(settings)


def get_korean_patch_enabled() -> bool:
    settings = load_settings()
    return bool(settings.get("korean_patch_enabled", False))


def set_korean_patch_enabled(enabled: bool) -> None:
    settings = load_settings()
    settings["korean_patch_enabled"] = bool(enabled)
    save_settings(settings)


def get_patch_cache_version() -> str:
    settings = load_settings()
    value = settings.get("patch_cache_version", "")
    return str(value) if value else ""


def set_patch_cache_version(version: str) -> None:
    settings = load_settings()
    settings["patch_cache_version"] = version
    save_settings(settings)


def get_patch_manager_version() -> str:
    settings = load_settings()
    value = settings.get("patch_manager_version", "")
    return str(value) if value else ""


def set_patch_manager_version(version: str) -> None:
    settings = load_settings()
    settings["patch_manager_version"] = version
    save_settings(settings)


def get_manager_shortcut_enabled() -> bool:
    settings = load_settings()
    return bool(settings.get("manager_shortcut_enabled", False))


def set_manager_shortcut_enabled(enabled: bool) -> None:
    settings = load_settings()
    settings["manager_shortcut_enabled"] = bool(enabled)
    save_settings(settings)


def get_ranked_shortcut_enabled() -> bool:
    settings = load_settings()
    return bool(settings.get("ranked_shortcut_enabled", False))


def set_ranked_shortcut_enabled(enabled: bool) -> None:
    settings = load_settings()
    settings["ranked_shortcut_enabled"] = bool(enabled)
    save_settings(settings)
