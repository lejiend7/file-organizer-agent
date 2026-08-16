"""Entry point: tray/menu-bar-first launch (docs/PRODUCT_SPEC.md section 14.1).

The app starts hidden in the tray; the pywebview window is created but
withdrawn (hidden) until the user opens it from the tray. This keeps a
single window instance alive rather than recreating it, since pywebview
does not support pausing a window's JS state between show/hide cycles
cheaply.
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

import webview

from organizer.platforms.base import PlatformAdapter
from organizer.ui.api import OrganizerApi

_WEB_DIR = Path(__file__).parent / "web"


def _make_adapter() -> PlatformAdapter:
    if sys.platform == "darwin":
        from organizer.platforms.macos.adapter import MacOSAdapter

        return MacOSAdapter()
    raise NotImplementedError(
        "Only the macOS adapter exists so far (Day 1). Windows support begins Day 2 - "
        "see docs/IMPLEMENTATION_PLAN.md."
    )


def _run_tray(window: webview.Window) -> None:
    """Best-effort system tray icon via pystray. If pystray or a display
    backend isn't available (e.g. headless CI), the app still runs with
    just the window - tray is a convenience, not a hard requirement.
    """
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        return

    def show_window(_icon=None, _item=None) -> None:
        window.show()

    def quit_app(icon, _item=None) -> None:
        icon.stop()
        window.destroy()

    image = Image.new("RGB", (64, 64), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((16, 16, 48, 48), fill="black")

    menu = pystray.Menu(
        pystray.MenuItem("Open dashboard", show_window, default=True),
        pystray.MenuItem("Quit", quit_app),
    )
    icon = pystray.Icon("file-organizer-agent", image, "File Organizer Agent", menu)
    icon.run()


def main() -> None:
    adapter = _make_adapter()
    api = OrganizerApi(adapter)

    window = webview.create_window(
        "File Organizer Agent",
        url=str(_WEB_DIR / "index.html"),
        js_api=api,
        width=960,
        height=600,
        min_size=(720, 480),
        hidden=True,  # tray-first: window starts hidden per docs/PRODUCT_SPEC.md 14.1
    )

    threading.Thread(target=_run_tray, args=(window,), daemon=True).start()
    webview.start()


if __name__ == "__main__":
    main()
