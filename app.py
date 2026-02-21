"""S2Ranked Manager desktop app."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
import traceback
import webbrowser
import ctypes
from pathlib import Path
from tkinter import (
    BOTH,
    DISABLED,
    LEFT,
    NORMAL,
    BooleanVar,
    Button,
    Checkbutton,
    Frame,
    Label,
    StringVar,
    Tk,
)

from config import APP_NAME, APP_VERSION, MANAGER_REPO_URL, RELEASES_URL, log_path
from github_release import ReleaseInfo, fetch_latest_release
from installer import (
    InstallError,
    build_layout,
    copy_self_into_s2ranked,
    detect_base_dir,
    install_latest_release,
)
from manager_settings import (
    get_installed_version,
    get_korean_patch_enabled,
    get_manager_shortcut_enabled,
    get_patch_manager_version,
    get_patch_cache_version,
    get_ranked_shortcut_enabled,
    set_installed_version,
    set_korean_patch_enabled,
    set_manager_shortcut_enabled,
    set_patch_manager_version,
    set_patch_cache_version,
    set_ranked_shortcut_enabled,
)
from self_update import SelfUpdateError, can_self_update, fetch_latest_manager_release, is_newer_version, prepare_self_update
from shortcuts import ShortcutError, apply_shortcuts


def configure_logging() -> None:
    lp = log_path()
    lp.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(lp, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def configure_windows_dpi() -> None:
    if os.name != "nt":
        return
    try:
        # Ensure Tk renders widgets correctly on high-DPI displays.
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


class ManagerApp:
    def __init__(self) -> None:
        self.base_dir: Path | None = None
        self.latest_release: ReleaseInfo | None = None
        self.current_version = get_installed_version()
        self.patch_cache_version = get_patch_cache_version()
        self.patch_manager_version = get_patch_manager_version()
        self.is_self_updating = False
        self.is_installing = False

        configure_windows_dpi()
        self.root = Tk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("720x340")
        self.root.minsize(720, 280)

        self.base_dir_var = StringVar(value="Detected: checking...")
        self.current_var = StringVar(value=f"Installed: {self._display_installed_version()}")
        self.latest_var = StringVar(value="Latest: checking...")
        self.status_var = StringVar(value="Initializing...")
        self.korean_patch_var = BooleanVar(value=get_korean_patch_enabled())
        self.manager_shortcut_var = BooleanVar(value=get_manager_shortcut_enabled())
        self.ranked_shortcut_var = BooleanVar(value=get_ranked_shortcut_enabled())

        self._build_ui()
        self.root.after(100, self.initialize)

    def _build_ui(self) -> None:
        frame = Frame(self.root, padx=14, pady=12)
        frame.pack(fill=BOTH, expand=True)

        Label(frame, text=APP_NAME, font=("Segoe UI", 20, "bold")).pack(anchor="w")
        Label(frame, textvariable=self.base_dir_var, font=("Segoe UI", 11)).pack(anchor="w", pady=(10, 2))
        Label(frame, textvariable=self.current_var, font=("Segoe UI", 12)).pack(anchor="w", pady=2)
        Label(frame, textvariable=self.latest_var, font=("Segoe UI", 12)).pack(anchor="w", pady=2)

        self.korean_patch_checkbox = Checkbutton(
            frame,
            text="Apply Korean patch (Experimental)",
            variable=self.korean_patch_var,
            command=self.on_korean_patch_toggled,
            state=DISABLED,
            font=("Segoe UI", 10),
        )
        self.korean_patch_checkbox.pack(anchor="w", pady=(10, 2))

        self.manager_shortcut_checkbox = Checkbutton(
            frame,
            text="Desktop shortcut: Manager",
            variable=self.manager_shortcut_var,
            command=self.on_manager_shortcut_toggled,
            state=DISABLED,
            font=("Segoe UI", 10),
        )
        self.manager_shortcut_checkbox.pack(anchor="w", pady=(2, 2))

        self.ranked_shortcut_checkbox = Checkbutton(
            frame,
            text="Desktop shortcut: S2Ranked",
            variable=self.ranked_shortcut_var,
            command=self.on_ranked_shortcut_toggled,
            state=DISABLED,
            font=("Segoe UI", 10),
        )
        self.ranked_shortcut_checkbox.pack(anchor="w", pady=(2, 2))

        Label(frame, textvariable=self.status_var, font=("Segoe UI", 10), fg="#333").pack(anchor="w", pady=(6, 0))

        buttons = Frame(frame)
        buttons.pack(anchor="w", pady=(8, 0))

        button_opts = {
            "font": ("Segoe UI", 10),
            "padx": 12,
            "pady": 4,
        }

        self.update_button = Button(
            buttons,
            text="Install / Update",
            state=DISABLED,
            command=self.on_update_clicked,
            **button_opts,
        )
        self.update_button.pack(side=LEFT, padx=(0, 8))

        self.refresh_button = Button(
            buttons,
            text="Refresh",
            command=self.on_refresh_clicked,
            **button_opts,
        )
        self.refresh_button.pack(side=LEFT, padx=(0, 8))

        self.release_button = Button(
            buttons,
            text="Ranked Releases",
            command=lambda: webbrowser.open(RELEASES_URL),
            **button_opts,
        )
        self.release_button.pack(side=LEFT, padx=(0, 8))

        self.repo_button = Button(
            buttons,
            text="Manager Repo",
            command=lambda: webbrowser.open(MANAGER_REPO_URL),
            **button_opts,
        )
        self.repo_button.pack(side=LEFT, padx=(0, 8))

        self.self_update_button = Button(
            buttons,
            text="Update Manager",
            command=self.on_self_update_clicked,
            state=NORMAL if can_self_update() else DISABLED,
            **button_opts,
        )
        self.self_update_button.pack(side=LEFT, padx=(0, 8))

        self.log_button = Button(
            buttons,
            text="Open Log",
            command=self.open_log,
            **button_opts,
        )
        self.log_button.pack(side=LEFT)

    def initialize(self) -> None:
        try:
            self.base_dir = detect_base_dir()
            self.base_dir_var.set(f"Detected: {self.base_dir}")
            self._invalidate_patch_cache_on_manager_version_change()
            self._detect_unknown_installed_version()
            self.current_var.set(f"Installed: {self._display_installed_version()}")
            self.korean_patch_checkbox.configure(state=NORMAL)
            self.manager_shortcut_checkbox.configure(state=NORMAL)
            self.ranked_shortcut_checkbox.configure(state=NORMAL)
        except Exception as exc:
            self.base_dir = None
            self.base_dir_var.set("Detected: not found")
            self.status_var.set(str(exc))
            self.update_button.configure(state=DISABLED)
            self.refresh_button.configure(state=NORMAL)
            self.korean_patch_checkbox.configure(state=DISABLED)
            self.manager_shortcut_checkbox.configure(state=DISABLED)
            self.ranked_shortcut_checkbox.configure(state=DISABLED)
            return

        try:
            target = copy_self_into_s2ranked(self.base_dir)
            if target is not None:
                logging.info("Copied executable to %s", target)
        except Exception:
            logging.exception("Failed to self-copy executable")

        self._apply_shortcut_preferences()

        self.status_var.set("Checking latest release...")
        self.update_button.configure(state=DISABLED)
        self.refresh_button.configure(state=DISABLED)
        threading.Thread(target=self._load_latest_release, daemon=True).start()

    def _load_latest_release(self) -> None:
        try:
            release = fetch_latest_release()
            self.latest_release = release
            self.root.after(0, lambda: self._apply_release_info(release))
        except Exception as exc:
            logging.exception("Failed to load latest release")
            self.root.after(0, lambda: self._set_error(f"Failed to fetch latest: {exc}"))

    def _apply_release_info(self, release: ReleaseInfo) -> None:
        latest = release.tag_name or "(unknown)"
        self.latest_var.set(f"Latest: {latest}")
        self.current_var.set(f"Installed: {self._display_installed_version()}")
        self.update_button.configure(state=NORMAL)
        self.refresh_button.configure(state=NORMAL)

        if not self.current_version:
            self.update_button.configure(text="Install")
        elif self.current_version == latest:
            self.update_button.configure(text="Reinstall")
        else:
            self.update_button.configure(text="Update")

        self.status_var.set("")

    def _set_error(self, message: str) -> None:
        self.status_var.set(message)
        self.update_button.configure(state=DISABLED)
        self.refresh_button.configure(state=NORMAL)

    def _display_installed_version(self) -> str:
        return self.current_version or "(not installed)"

    def _detect_unknown_installed_version(self) -> None:
        if self.base_dir is None or self.current_version:
            return
        layout = build_layout(self.base_dir)
        if layout.mod_pack_dir.exists() and any(layout.mod_pack_dir.iterdir()):
            self.current_version = "(unknown)"

    def _invalidate_patch_cache_on_manager_version_change(self) -> None:
        if self.base_dir is None:
            return
        if self.patch_manager_version == APP_VERSION:
            return

        layout = build_layout(self.base_dir)
        if layout.mod_patched_cache_dir.exists():
            logging.info(
                "Manager version changed (%s -> %s). Invalidating patched cache at %s",
                self.patch_manager_version or "(unset)",
                APP_VERSION,
                layout.mod_patched_cache_dir,
            )
            try:
                shutil.rmtree(layout.mod_patched_cache_dir, ignore_errors=True)
            except Exception:
                logging.exception("Failed to invalidate patched cache")

        set_patch_cache_version("")
        self.patch_cache_version = ""
        set_patch_manager_version(APP_VERSION)
        self.patch_manager_version = APP_VERSION

    def on_refresh_clicked(self) -> None:
        if self.is_installing:
            return
        self.latest_release = None
        self.latest_var.set("Latest: checking...")
        self.status_var.set("Refreshing...")
        self.initialize()

    def on_update_clicked(self) -> None:
        if self.base_dir is None or self.latest_release is None or self.is_self_updating:
            return
        self.is_installing = True
        self.update_button.configure(state=DISABLED)
        self.refresh_button.configure(state=DISABLED)
        self.korean_patch_checkbox.configure(state=DISABLED)
        self.manager_shortcut_checkbox.configure(state=DISABLED)
        self.ranked_shortcut_checkbox.configure(state=DISABLED)
        self.status_var.set("Installing / updating...")
        threading.Thread(target=self._run_install, daemon=True).start()

    def on_self_update_clicked(self) -> None:
        if self.is_installing or self.is_self_updating:
            return
        self.is_self_updating = True
        self.self_update_button.configure(state=DISABLED)
        self.update_button.configure(state=DISABLED)
        self.refresh_button.configure(state=DISABLED)
        self.korean_patch_checkbox.configure(state=DISABLED)
        self.manager_shortcut_checkbox.configure(state=DISABLED)
        self.ranked_shortcut_checkbox.configure(state=DISABLED)
        self.status_var.set("Checking manager updates...")
        threading.Thread(target=self._run_self_update, daemon=True).start()

    def _run_self_update(self) -> None:
        try:
            latest = fetch_latest_manager_release()
            if not is_newer_version(latest.tag_name, APP_VERSION):
                self.root.after(0, lambda: self._self_update_finished("Manager is already up to date."))
                return
            version = prepare_self_update(latest)
            self.root.after(0, lambda: self._self_update_restart(version))
        except (SelfUpdateError, InstallError) as exc:
            self.root.after(0, lambda: self._self_update_finished(f"Manager update failed: {exc}"))
        except Exception as exc:
            logging.exception("Manager self-update failed")
            detail = "".join(traceback.format_exception_only(type(exc), exc)).strip()
            self.root.after(0, lambda: self._self_update_finished(f"Manager update failed: {detail}"))

    def _self_update_finished(self, message: str) -> None:
        self.is_self_updating = False
        self.status_var.set(message)
        self.refresh_button.configure(state=NORMAL)
        self.update_button.configure(state=NORMAL)
        self.korean_patch_checkbox.configure(state=NORMAL)
        self.manager_shortcut_checkbox.configure(state=NORMAL)
        self.ranked_shortcut_checkbox.configure(state=NORMAL)
        if can_self_update():
            self.self_update_button.configure(state=NORMAL)

    def _self_update_restart(self, version: str) -> None:
        self.status_var.set(f"Manager update prepared ({version}). Restarting...")
        self.root.update_idletasks()
        self.root.after(150, self._exit_for_self_update)

    def _exit_for_self_update(self) -> None:
        try:
            self.root.destroy()
        finally:
            os._exit(0)

    def _run_install(self) -> None:
        try:
            layout = build_layout(self.base_dir)
            use_patch = bool(self.korean_patch_var.get())
            install_latest_release(self.latest_release, layout, use_korean_patch=use_patch)

            version = self.latest_release.tag_name or ""
            set_patch_manager_version(APP_VERSION)
            self.patch_manager_version = APP_VERSION
            if version:
                set_installed_version(version)
                set_patch_cache_version(version)
                self.current_version = version
                self.patch_cache_version = version

            self.root.after(0, self._install_succeeded)
        except InstallError as exc:
            logging.exception("Install failed")
            self.root.after(0, lambda: self._install_failed(str(exc)))
        except Exception as exc:
            logging.exception("Install failed")
            detail = "".join(traceback.format_exception_only(type(exc), exc)).strip()
            self.root.after(0, lambda: self._install_failed(detail))

    def _install_succeeded(self) -> None:
        self.is_installing = False
        self.current_var.set(f"Installed: {self._display_installed_version()}")
        self.status_var.set("Install/update complete")
        if self.latest_release and self.current_version == self.latest_release.tag_name:
            self.update_button.configure(text="Reinstall")
        self.update_button.configure(state=NORMAL)
        self.refresh_button.configure(state=NORMAL)
        self.korean_patch_checkbox.configure(state=NORMAL)
        self.manager_shortcut_checkbox.configure(state=NORMAL)
        self.ranked_shortcut_checkbox.configure(state=NORMAL)
        self._apply_shortcut_preferences()

    def _install_failed(self, message: str) -> None:
        self.is_installing = False
        self.status_var.set(f"Failed: {message}")
        self.update_button.configure(state=NORMAL)
        self.refresh_button.configure(state=NORMAL)
        self.korean_patch_checkbox.configure(state=NORMAL)
        self.manager_shortcut_checkbox.configure(state=NORMAL)
        self.ranked_shortcut_checkbox.configure(state=NORMAL)

    def on_korean_patch_toggled(self) -> None:
        enabled = bool(self.korean_patch_var.get())
        set_korean_patch_enabled(enabled)

    def _apply_shortcut_preferences(
        self,
        *,
        delete_manager_when_disabled: bool = False,
        delete_ranked_when_disabled: bool = False,
    ) -> bool:
        if self.base_dir is None:
            return False
        manager_enabled = bool(self.manager_shortcut_var.get())
        ranked_enabled = bool(self.ranked_shortcut_var.get())
        try:
            apply_shortcuts(
                self.base_dir,
                manager_enabled=manager_enabled,
                ranked_enabled=ranked_enabled,
                delete_manager_when_disabled=delete_manager_when_disabled,
                delete_ranked_when_disabled=delete_ranked_when_disabled,
            )
            return True
        except ShortcutError as exc:
            self.status_var.set(str(exc))
            return False
        except Exception:
            logging.exception("Failed to apply shortcut preferences")
            self.status_var.set("Failed to apply shortcut preferences. Check log for details.")
            return False

    def on_manager_shortcut_toggled(self) -> None:
        new_value = bool(self.manager_shortcut_var.get())
        old_value = get_manager_shortcut_enabled()
        set_manager_shortcut_enabled(new_value)
        if not self._apply_shortcut_preferences(delete_manager_when_disabled=True):
            set_manager_shortcut_enabled(old_value)
            self.manager_shortcut_var.set(old_value)

    def on_ranked_shortcut_toggled(self) -> None:
        new_value = bool(self.ranked_shortcut_var.get())
        old_value = get_ranked_shortcut_enabled()
        set_ranked_shortcut_enabled(new_value)
        if not self._apply_shortcut_preferences(delete_ranked_when_disabled=True):
            set_ranked_shortcut_enabled(old_value)
            self.ranked_shortcut_var.set(old_value)

    def open_log(self) -> None:
        path = log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("", encoding="utf-8")

        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", str(path)], check=False)
            else:
                subprocess.run(["xdg-open", str(path)], check=False)
        except Exception:
            logging.exception("Failed to open log file")

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    configure_logging()
    app = ManagerApp()
    app.run()


if __name__ == "__main__":
    main()
