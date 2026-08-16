"""Content fingerprint cache so we don't re-process an unchanged file.

Used both by the core organizing pipeline (skip files already handled) and
by the AI layer (skip re-analyzing an unchanged file, per
docs/PRODUCT_SPEC.md section 9). Uses size + mtime + a partial content hash
rather than a full-file hash, since full hashing every large video file on
every watcher tick would be needlessly slow - this is a change-detector,
not a cryptographic integrity check.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

_PARTIAL_READ_BYTES = 65536


def compute_fingerprint(path: Path) -> str | None:
    try:
        stat = path.stat()
        with path.open("rb") as f:
            chunk = f.read(_PARTIAL_READ_BYTES)
    except OSError:
        return None

    hasher = hashlib.sha256()
    hasher.update(str(stat.st_size).encode())
    hasher.update(str(int(stat.st_mtime)).encode())
    hasher.update(chunk)
    return hasher.hexdigest()


class FingerprintCache:
    """JSON-backed map of absolute path -> last-seen fingerprint."""

    def __init__(self, cache_file: Path) -> None:
        self._cache_file = cache_file
        self._data: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if self._cache_file.exists():
            try:
                self._data = json.loads(self._cache_file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self._data = {}

    def save(self) -> None:
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._cache_file.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def is_unchanged(self, path: Path) -> bool:
        fp = compute_fingerprint(path)
        if fp is None:
            return False
        return self._data.get(str(path.resolve())) == fp

    def record(self, path: Path) -> None:
        fp = compute_fingerprint(path)
        if fp is not None:
            self._data[str(path.resolve())] = fp

    def forget(self, path: Path) -> None:
        self._data.pop(str(path.resolve()), None)
