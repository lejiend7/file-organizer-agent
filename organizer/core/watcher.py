"""Filesystem monitoring via watchdog, wired into the organizing pipeline.

Never contains platform-specific logic - watchdog itself abstracts macOS
(FSEvents) vs Windows (ReadDirectoryChangesW) file system APIs. This module
just owns the polling loop that repeatedly retries files still settling
(see StabilityTracker) and calls back into the UI layer with outcomes.
"""
from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from organizer.core.config import AppConfig
from organizer.core.fingerprint import FingerprintCache
from organizer.core.pipeline import OrganizeResult, organize_file
from organizer.core.stability import StabilityTracker

OrganizeCallback = Callable[[OrganizeResult], None]


class _Handler(FileSystemEventHandler):
    def __init__(self, pending: set[Path], lock: threading.Lock) -> None:
        self._pending = pending
        self._lock = lock

    def _track(self, path_str: str) -> None:
        path = Path(path_str)
        with self._lock:
            self._pending.add(path)

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._track(event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._track(event.src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._track(event.dest_path)


class OrganizerWatcher:
    """Watches config.source_folder and organizes files as they settle.

    Usage:
        watcher = OrganizerWatcher(config, logger, fingerprint_cache, on_result=ui.handle)
        watcher.start()
        ...
        watcher.stop()
    """

    def __init__(
        self,
        config: AppConfig,
        logger: logging.Logger,
        fingerprint_cache: FingerprintCache | None = None,
        on_result: OrganizeCallback | None = None,
        poll_interval_seconds: float = 1.0,
    ) -> None:
        self._config = config
        self._logger = logger
        self._fingerprint_cache = fingerprint_cache
        self._on_result = on_result
        self._poll_interval = poll_interval_seconds

        self._pending: set[Path] = set()
        self._lock = threading.Lock()
        self._stability = StabilityTracker()
        self._observer: Observer | None = None
        self._poll_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    @property
    def is_running(self) -> bool:
        return self._observer is not None and self._observer.is_alive()

    def start(self) -> None:
        if self.is_running:
            return
        if self._config.source_folder is None:
            raise ValueError("cannot start watcher: no source_folder configured")

        self._stop_event.clear()
        handler = _Handler(self._pending, self._lock)
        self._observer = Observer()
        self._observer.schedule(handler, str(self._config.source_folder), recursive=False)
        self._observer.start()

        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
        if self._poll_thread is not None:
            self._poll_thread.join(timeout=5)
            self._poll_thread = None

    def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
            with self._lock:
                candidates = list(self._pending)
            for path in candidates:
                result = organize_file(
                    path,
                    self._config,
                    self._logger,
                    fingerprint_cache=self._fingerprint_cache,
                    stability=self._stability,
                )
                if result.outcome != "pending_stability":
                    with self._lock:
                        self._pending.discard(path)
                    self._stability.forget(path)
                    if self._on_result is not None:
                        self._on_result(result)
            time.sleep(self._poll_interval)
