"""Waits until a file's size and modification time stop changing.

Prevents organizing a file that's still being written (download in
progress, editor autosave, cloud-sync placeholder) and helps detect files
locked by another application. See docs/PRODUCT_SPEC.md section 8.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class _Snapshot:
    size: int
    mtime: float


def _snapshot(path: Path) -> _Snapshot | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return _Snapshot(size=stat.st_size, mtime=stat.st_mtime)


def is_locked(path: Path) -> bool:
    """Best-effort check for a file locked/held open by another process.

    Attempts a non-destructive open in read+append mode, which fails on
    most platforms if another process holds an exclusive lock. This is a
    heuristic, not a guarantee - true lock detection is platform-specific
    and belongs in a platform adapter if it needs to get more precise.
    """
    try:
        with path.open("rb"):
            return False
    except OSError:
        return True


def wait_until_stable(
    path: Path,
    checks: int = 2,
    interval_seconds: float = 1.0,
    timeout_seconds: float = 30.0,
) -> bool:
    """Poll `path` until size and mtime are unchanged across `checks` samples.

    Returns True if the file settled within timeout_seconds, False if the
    timeout was hit (still changing) or the file disappeared. Callers should
    treat False as "leave it alone for now, try again later" - never force
    an action on an unstable file.
    """
    deadline = time.monotonic() + timeout_seconds
    last = _snapshot(path)
    if last is None:
        return False

    stable_count = 1
    while time.monotonic() < deadline:
        time.sleep(interval_seconds)
        current = _snapshot(path)
        if current is None:
            return False
        if current == last:
            stable_count += 1
            if stable_count >= checks:
                return True
        else:
            stable_count = 1
            last = current
    return False


class StabilityTracker:
    """Non-blocking alternative to wait_until_stable, for use inside an
    event loop (e.g. the watcher) where sleeping would block other events.

    Call `observe(path)` on each poll tick; it returns True once the path
    has reported the same size/mtime on `checks` consecutive observations.
    """

    def __init__(self, checks: int = 2) -> None:
        self._checks = checks
        self._last: dict[Path, _Snapshot] = {}
        self._counts: dict[Path, int] = {}

    def observe(self, path: Path) -> bool:
        current = _snapshot(path)
        if current is None:
            self._last.pop(path, None)
            self._counts.pop(path, None)
            return False

        previous = self._last.get(path)
        if previous == current:
            self._counts[path] = self._counts.get(path, 1) + 1
        else:
            self._counts[path] = 1
            self._last[path] = current

        return self._counts[path] >= self._checks

    def forget(self, path: Path) -> None:
        self._last.pop(path, None)
        self._counts.pop(path, None)
