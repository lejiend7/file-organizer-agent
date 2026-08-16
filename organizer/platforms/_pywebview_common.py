"""Folder selection shared by both platform adapters.

pywebview's own file dialog is already cross-platform, so there's no OS-
specific dialog code to write per-platform - see docs/ARCHITECTURE.md
section 2 for why this still sits behind the PlatformAdapter interface
rather than being called directly from the UI.
"""
from __future__ import annotations

from pathlib import Path


def select_folder_via_pywebview(title: str) -> Path | None:
    import webview  # imported lazily so this module is importable without a display/window

    window = webview.active_window()
    if window is None:
        return None

    result = window.create_file_dialog(webview.FOLDER_DIALOG, directory="", allow_multiple=False)
    if not result:
        return None
    return Path(result[0])
