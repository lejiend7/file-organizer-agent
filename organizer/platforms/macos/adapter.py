"""macOS platform adapter. Day 1 target platform - see docs/PRODUCT_SPEC.md
section 2 and docs/IMPLEMENTATION_PLAN.md.

Never requires admin/root. Credentials go through the `keyring` package,
which targets macOS Keychain automatically on this platform.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import keyring

from organizer.platforms._pywebview_common import select_folder_via_pywebview

_KEYRING_SERVICE = "File Organizer Agent"
_LAUNCH_AGENT_LABEL = "com.fileorganizeragent.launcher"

# macOS forbids ':' in Finder-visible names and NUL in all filenames.
_MACOS_INVALID_CHARS = re.compile(r"[:\x00]")


class MacOSAdapter:
    def app_data_dir(self) -> Path:
        return Path.home() / "Library" / "Application Support" / "File Organizer Agent"

    def select_folder(self, title: str) -> Path | None:
        return select_folder_via_pywebview(title)

    def store_credential(self, key: str, value: str) -> None:
        keyring.set_password(_KEYRING_SERVICE, key, value)

    def get_credential(self, key: str) -> str | None:
        return keyring.get_password(_KEYRING_SERVICE, key)

    def delete_credential(self, key: str) -> None:
        try:
            keyring.delete_password(_KEYRING_SERVICE, key)
        except keyring.errors.PasswordDeleteError:
            pass  # already absent - deletion is idempotent from the caller's view

    def _launch_agent_path(self) -> Path:
        return Path.home() / "Library" / "LaunchAgents" / f"{_LAUNCH_AGENT_LABEL}.plist"

    def set_launch_at_login(self, enabled: bool) -> None:
        plist_path = self._launch_agent_path()
        if not enabled:
            if plist_path.exists():
                plist_path.unlink()
            return

        executable = _resolve_bundled_executable()
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        plist_path.write_text(
            f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{_LAUNCH_AGENT_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{executable}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>ProcessType</key>
    <string>Interactive</string>
</dict>
</plist>
""",
            encoding="utf-8",
        )

    def is_launch_at_login_enabled(self) -> bool:
        return self._launch_agent_path().exists()

    def notify(self, title: str, message: str) -> None:
        # osascript is available on every macOS install with no extra
        # dependency; message content must already be safe (no file
        # content/credentials) by the time it reaches this adapter.
        script = f'display notification "{_escape_applescript(message)}" with title "{_escape_applescript(title)}"'
        subprocess.run(["osascript", "-e", script], check=False, capture_output=True)

    def validate_filename(self, name: str) -> bool:
        if not name or name in (".", ".."):
            return False
        if _MACOS_INVALID_CHARS.search(name):
            return False
        if len(name.encode("utf-8")) > 255:
            return False
        return True


def _resolve_bundled_executable() -> str:
    # Set by the packaged .app at build time; falls back to the current
    # interpreter during development so launch-at-login is testable unpackaged.
    return os.environ.get("FILE_ORGANIZER_AGENT_EXECUTABLE", "/usr/bin/env python3 -m organizer.ui.app")


def _escape_applescript(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')
