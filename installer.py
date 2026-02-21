"""Installation workflow for Spelunky Ranked payloads."""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path

from config import (
    MANAGER_EXE_NAME,
    MODLUNKY_INSTALL_DIR_KEY,
    PERSISTENT_S2RANKED_FILES,
    S2RANKED_ZIP_NAME,
    SPELUNKY_RANKED_ZIP_NAME,
    modlunky_config_path,
)
from github_release import ReleaseInfo, download_file
from korean_patch import patch_mod_dir


class InstallError(RuntimeError):
    pass


@dataclass
class InstallLayout:
    base_dir: Path
    s2ranked_dir: Path
    downloads_dir: Path
    mod_pack_dir: Path

    @property
    def mod_cache_dir(self) -> Path:
        return self.downloads_dir / "SpelunkyRanked"

    @property
    def mod_patched_cache_dir(self) -> Path:
        return self.downloads_dir / "SpelunkyRanked_patched"


def detect_base_dir() -> Path:
    config_path = modlunky_config_path()
    if not config_path.exists():
        raise InstallError(
            "Modlunky config file was not found. Run Modlunky once before using this manager.\n"
            f"Expected: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    install_dir = payload.get(MODLUNKY_INSTALL_DIR_KEY, "")
    if not isinstance(install_dir, str) or not install_dir.strip():
        raise InstallError(
            "Modlunky config is missing 'install-dir'. Open Modlunky and complete setup first."
        )

    base_dir = Path(install_dir).expanduser().resolve()
    if not base_dir.exists():
        raise InstallError(f"Spelunky 2 install directory does not exist: {base_dir}")
    return base_dir


def build_layout(base_dir: Path) -> InstallLayout:
    return InstallLayout(
        base_dir=base_dir,
        s2ranked_dir=base_dir / "S2Ranked",
        downloads_dir=base_dir / "S2Ranked" / "Downloads",
        mod_pack_dir=base_dir / "Mods" / "Packs" / "SpelunkyRanked",
    )


def ensure_layout(layout: InstallLayout) -> None:
    layout.s2ranked_dir.mkdir(parents=True, exist_ok=True)
    layout.downloads_dir.mkdir(parents=True, exist_ok=True)
    layout.mod_pack_dir.mkdir(parents=True, exist_ok=True)


def clean_downloads(downloads_dir: Path) -> None:
    if downloads_dir.exists():
        shutil.rmtree(downloads_dir)
    downloads_dir.mkdir(parents=True, exist_ok=True)


def install_latest_release(release: ReleaseInfo, layout: InstallLayout, use_korean_patch: bool) -> None:
    ensure_layout(layout)
    _stop_s2ranked_if_running()
    clean_downloads(layout.downloads_dir)

    s2ranked_asset = release.asset_by_name(S2RANKED_ZIP_NAME)
    mod_asset = release.asset_by_name(SPELUNKY_RANKED_ZIP_NAME)
    if s2ranked_asset is None or mod_asset is None:
        raise InstallError(
            f"Required release assets are missing: {S2RANKED_ZIP_NAME}, {SPELUNKY_RANKED_ZIP_NAME}"
        )

    s2ranked_zip = layout.downloads_dir / s2ranked_asset.name
    mod_zip = layout.downloads_dir / mod_asset.name

    download_file(s2ranked_asset.download_url, s2ranked_zip)
    download_file(mod_asset.download_url, mod_zip)

    with tempfile.TemporaryDirectory(prefix="s2ranked_manager_") as temp_raw:
        temp_dir = Path(temp_raw)
        mod_extract = temp_dir / "mod_extract"
        s2_extract = temp_dir / "s2_extract"
        _extract_zip(mod_zip, mod_extract)
        _extract_zip(s2ranked_zip, s2_extract)

        mod_source = _find_payload_root(mod_extract, "SpelunkyRanked")
        s2_source = _find_payload_root(s2_extract, "S2Ranked")

        patch_available = _prepare_mod_variants(layout, mod_source)
        _apply_mod_variant(layout, use_korean_patch, patch_available)
        _merge_s2ranked_preserving_user_files(layout.s2ranked_dir, s2_source)

    apply_post_install_patches(layout.base_dir)


def _stop_s2ranked_if_running(timeout_sec: float = 8.0) -> None:
    if os.name != "nt":
        return

    exe_name = "S2Ranked.exe"
    if not _is_process_running(exe_name):
        return

    logging.info("Detected running process: %s. Stopping it before install/update.", exe_name)
    result = subprocess.run(
        ["taskkill", "/IM", exe_name, "/T", "/F"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in (0, 128):
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        detail = stderr or stdout or f"taskkill exit code {result.returncode}"
        raise InstallError(f"Failed to stop {exe_name}: {detail}")

    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        if not _is_process_running(exe_name):
            return
        time.sleep(0.2)

    raise InstallError(
        f"{exe_name} is still running. Close it manually and try install/update again."
    )


def _is_process_running(exe_name: str) -> bool:
    result = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {exe_name}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise InstallError(f"Could not query running processes: {stderr or 'tasklist failed'}")
    return exe_name.lower() in (result.stdout or "").lower()


def _extract_zip(zip_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(destination)


def _find_payload_root(extracted_root: Path, expected_name: str) -> Path:
    candidate = extracted_root / expected_name
    if candidate.is_dir():
        return candidate

    dirs = [p for p in extracted_root.rglob("*") if p.is_dir() and p.name == expected_name]
    if dirs:
        return dirs[0]
    return extracted_root


def _replace_directory(destination: Path, source: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def _prepare_mod_variants(layout: InstallLayout, mod_source: Path) -> bool:
    _replace_directory(layout.mod_cache_dir, mod_source)
    _replace_directory(layout.mod_patched_cache_dir, layout.mod_cache_dir)
    patched_ok = patch_mod_dir(layout.mod_patched_cache_dir)
    if not patched_ok:
        shutil.rmtree(layout.mod_patched_cache_dir, ignore_errors=True)
    return patched_ok


def _apply_mod_variant(layout: InstallLayout, use_korean_patch: bool, patch_available: bool) -> None:
    if use_korean_patch and not patch_available:
        raise InstallError(
            "Korean patch could not be applied for this release. main.lua may have changed."
        )
    source = layout.mod_patched_cache_dir if use_korean_patch else layout.mod_cache_dir
    _replace_directory(layout.mod_pack_dir, source)


def apply_cached_mod_variant(layout: InstallLayout, use_korean_patch: bool) -> None:
    ensure_layout(layout)
    if not layout.mod_cache_dir.exists():
        raise InstallError("Patch cache is missing. Run install/update first.")
    if use_korean_patch and not layout.mod_patched_cache_dir.exists():
        raise InstallError(
            "Korean patch cache is missing for the current version. Run install/update again."
        )

    source = layout.mod_patched_cache_dir if use_korean_patch else layout.mod_cache_dir
    _replace_directory(layout.mod_pack_dir, source)


def _merge_s2ranked_preserving_user_files(destination: Path, source: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)

    for item in list(destination.iterdir()):
        if item.name in PERSISTENT_S2RANKED_FILES:
            continue
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink(missing_ok=True)
        except PermissionError:
            logging.warning("Skipping locked path during cleanup: %s", item)
        except OSError:
            logging.warning("Skipping undeletable path during cleanup: %s", item)

    for item in source.iterdir():
        if item.name in PERSISTENT_S2RANKED_FILES:
            continue
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def apply_post_install_patches(base_dir: Path) -> None:
    """Reserved hook for future Lua/config patching steps."""
    _ = base_dir


def copy_self_into_s2ranked(base_dir: Path) -> Path | None:
    if not getattr(sys, "frozen", False):
        return None

    source = Path(sys.executable).resolve()
    target_dir = base_dir / "S2Ranked"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / MANAGER_EXE_NAME

    if source == target:
        return target

    shutil.copy2(source, target)
    return target
