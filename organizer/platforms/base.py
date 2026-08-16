"""Platform adapter interface. organizer/core, organizer/ai, organizer/review,
and organizer/ui depend only on this shape - never on organizer/platforms/macos
or organizer/platforms/windows directly. See docs/ARCHITECTURE.md section 2.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol


class PlatformAdapter(Protocol):
    def app_data_dir(self) -> Path:
        """Where config, logs, and caches live. Never beside the executable.
        macOS: ~/Library/Application Support/File Organizer Agent/
        Windows: %APPDATA%\\File Organizer Agent\\
        """
        ...

    def select_folder(self, title: str) -> Path | None:
        """Open a native folder picker. Returns None if the user cancels."""
        ...

    def store_credential(self, key: str, value: str) -> None:
        """Store a secret in the OS keyring. Never write credentials to
        the YAML config or to logs."""
        ...

    def get_credential(self, key: str) -> str | None:
        ...

    def delete_credential(self, key: str) -> None:
        ...

    def set_launch_at_login(self, enabled: bool) -> None:
        """Never requires admin/root privileges."""
        ...

    def is_launch_at_login_enabled(self) -> bool:
        ...

    def notify(self, title: str, message: str) -> None:
        """Native OS notification. Message must never contain file content
        or credentials."""
        ...

    def validate_filename(self, name: str) -> bool:
        """Platform-specific filename legality check (reserved names,
        invalid characters, length). Used in addition to, never instead of,
        organizer.ai.validator's cross-platform-safe checks."""
        ...
