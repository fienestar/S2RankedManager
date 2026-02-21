"""Desktop shortcut helpers."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from config import MANAGER_EXE_NAME


class ShortcutError(RuntimeError):
    pass


def _desktop_dir() -> Path:
    home = Path.home()
    return home / "Desktop"


def _ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _create_shortcut(shortcut_path: Path, target_path: Path, working_dir: Path) -> None:
    command = (
        "$WshShell = New-Object -ComObject WScript.Shell; "
        f"$Shortcut = $WshShell.CreateShortcut({_ps_quote(str(shortcut_path))}); "
        f"$Shortcut.TargetPath = {_ps_quote(str(target_path))}; "
        f"$Shortcut.WorkingDirectory = {_ps_quote(str(working_dir))}; "
        f"$Shortcut.IconLocation = {_ps_quote(str(target_path))}; "
        "$Shortcut.Save()"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "unknown error").strip()
        raise ShortcutError(f"Failed to create shortcut: {detail}")


def _remove_shortcut(path: Path) -> None:
    path.unlink(missing_ok=True)


def apply_shortcuts(
    base_dir: Path,
    manager_enabled: bool,
    ranked_enabled: bool,
    *,
    delete_manager_when_disabled: bool = False,
    delete_ranked_when_disabled: bool = False,
) -> None:
    if os.name != "nt":
        raise ShortcutError("Desktop shortcut toggles are only supported on Windows.")

    desktop = _desktop_dir()
    desktop.mkdir(parents=True, exist_ok=True)

    manager_shortcut = desktop / "S2Ranked Manager.lnk"
    ranked_shortcut = desktop / "S2Ranked.lnk"

    manager_target = base_dir / "S2Ranked" / MANAGER_EXE_NAME
    ranked_target = base_dir / "S2Ranked" / "S2Ranked.exe"

    if manager_enabled:
        if not manager_target.exists():
            raise ShortcutError(f"Manager executable not found: {manager_target}")
        _create_shortcut(manager_shortcut, manager_target, manager_target.parent)
    elif delete_manager_when_disabled:
        _remove_shortcut(manager_shortcut)

    if ranked_enabled:
        if not ranked_target.exists():
            raise ShortcutError(f"Ranked executable not found: {ranked_target}")
        _create_shortcut(ranked_shortcut, ranked_target, ranked_target.parent)
    elif delete_ranked_when_disabled:
        _remove_shortcut(ranked_shortcut)
