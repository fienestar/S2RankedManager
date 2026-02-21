"""Self-update helpers for the manager executable."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from config import MANAGER_EXE_NAME, MANAGER_LATEST_RELEASE_API, runtime_dir
from github_release import ReleaseInfo, download_file, fetch_latest_release_from_api


class SelfUpdateError(RuntimeError):
    pass


def fetch_latest_manager_release(timeout: int = 20) -> ReleaseInfo:
    return fetch_latest_release_from_api(MANAGER_LATEST_RELEASE_API, timeout=timeout)


def _parse_version(value: str) -> tuple[int, ...]:
    nums = [int(part) for part in re.findall(r"\d+", value or "")]
    return tuple(nums)


def is_newer_version(latest_tag: str, current_version: str) -> bool:
    latest = _parse_version(latest_tag)
    current = _parse_version(current_version)
    if latest and current:
        return latest > current
    return (latest_tag or "").strip() != (current_version or "").strip()


def can_self_update() -> bool:
    return bool(getattr(sys, "frozen", False)) and os.name == "nt"


def prepare_self_update(latest_release: ReleaseInfo) -> str:
    if not can_self_update():
        raise SelfUpdateError("Self-update is only available in Windows frozen executable mode.")

    current_exe = Path(sys.executable).resolve()
    if current_exe.name.lower() != MANAGER_EXE_NAME.lower():
        raise SelfUpdateError(f"Current executable name is unexpected: {current_exe.name}")

    asset = latest_release.asset_by_name(MANAGER_EXE_NAME)
    if asset is None:
        raise SelfUpdateError(f"Manager release is missing required asset: {MANAGER_EXE_NAME}")

    target_dir = runtime_dir()
    new_exe = target_dir / f"{MANAGER_EXE_NAME}.new"
    updater_cmd = target_dir / "manager_self_update.cmd"

    download_file(asset.download_url, new_exe)

    pid = os.getpid()
    script = (
        "@echo off\n"
        "setlocal\n"
        f"set \"TARGET={current_exe}\"\n"
        f"set \"NEW={new_exe}\"\n"
        "set /a WAITCOUNT=0\n"
        ":waitloop\n"
        f"tasklist /FI \"PID eq {pid}\" 2>NUL | find \"{pid}\" >NUL\n"
        "if not errorlevel 1 (\n"
        "  timeout /t 1 /nobreak >NUL\n"
        "  set /a WAITCOUNT+=1\n"
        "  if %WAITCOUNT% LSS 90 goto waitloop\n"
        ")\n"
        "move /Y \"%NEW%\" \"%TARGET%\" >NUL\n"
        "start \"\" \"%TARGET%\"\n"
        "del \"%~f0\"\n"
    )
    updater_cmd.write_text(script, encoding="utf-8")

    subprocess.Popen(
        ["cmd.exe", "/c", str(updater_cmd)],
        creationflags=getattr(subprocess, "DETACHED_PROCESS", 0)
        | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        close_fds=True,
    )
    return latest_release.tag_name or "(unknown)"
