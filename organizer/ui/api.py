"""JS-Python bridge exposed to the pywebview window as `window.pywebview.api`.

Every method here is the only path from the UI into the shared core - the
web layer never touches organizer/core, organizer/ai, or organizer/review
directly, which is what keeps the UI swappable (docs/PRODUCT_SPEC.md
section 14).
"""
from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

from organizer.ai.mock_provider import MockProvider
from organizer.ai.provider import AIProvider
from organizer.ai.validator import validate_recommendation
from organizer.core.config import AppConfig, load_config, save_config
from organizer.core.fingerprint import FingerprintCache
from organizer.core.logger import get_logger
from organizer.core.pipeline import OrganizeResult
from organizer.core.watcher import OrganizerWatcher
from organizer.platforms.base import PlatformAdapter
from organizer.review.queue import ReviewQueue


class OrganizerApi:
    def __init__(self, adapter: PlatformAdapter, ai_provider: AIProvider | None = None) -> None:
        self._adapter = adapter
        self._data_dir = adapter.app_data_dir()
        self._config_path = self._data_dir / "config.yaml"
        self._config: AppConfig = load_config(self._config_path)
        self._logger: logging.Logger = get_logger(self._data_dir / "logs")
        self._fingerprint_cache = FingerprintCache(self._data_dir / "fingerprints.json")
        self._review_queue = ReviewQueue(self._data_dir / "review_queue.json")
        self._ai_provider: AIProvider = ai_provider or MockProvider()
        self._watcher: OrganizerWatcher | None = None
        self._recent_activity: list[OrganizeResult] = []

    # ----- state -----

    def get_state(self) -> dict[str, Any]:
        return {
            "monitoring": self._watcher is not None and self._watcher.is_running,
            "source_folder": str(self._config.source_folder) if self._config.source_folder else None,
            "destination_folder": str(self._config.destination_folder) if self._config.destination_folder else None,
            "dry_run": self._config.dry_run,
            "ai_enabled": self._config.ai_enabled,
            "review_count": len(self._review_queue.list_pending()),
            "recent_activity": [
                {"path": str(r.path), "outcome": r.outcome, "destination": str(r.destination) if r.destination else None}
                for r in self._recent_activity[-20:]
            ],
        }

    # ----- folders -----

    def select_source_folder(self) -> dict[str, Any]:
        folder = self._adapter.select_folder("Choose a source folder")
        if folder is None:
            return {"ok": False}
        warning = None
        if self._config.destination_folder and self._is_inside(self._config.destination_folder, folder):
            warning = "destination_inside_source"
        self._config.source_folder = folder
        save_config(self._config, self._config_path)
        return {"ok": True, "path": str(folder), "warning": warning}

    def select_destination_folder(self) -> dict[str, Any]:
        folder = self._adapter.select_folder("Choose a destination folder")
        if folder is None:
            return {"ok": False}
        warning = None
        if self._config.source_folder and self._is_inside(self._config.source_folder, folder):
            warning = "destination_inside_source"
        self._config.destination_folder = folder
        save_config(self._config, self._config_path)
        return {"ok": True, "path": str(folder), "warning": warning}

    @staticmethod
    def _is_inside(source: Path, destination: Path) -> bool:
        try:
            destination.resolve().relative_to(source.resolve())
            return True
        except ValueError:
            return False

    # ----- monitoring -----

    def start_monitoring(self) -> dict[str, Any]:
        if not self._config.source_folder or not self._config.destination_folder:
            return {"ok": False, "error": "select both folders first"}
        if self._watcher is None:
            self._watcher = OrganizerWatcher(
                self._config, self._logger, self._fingerprint_cache, on_result=self._recent_activity.append
            )
        self._watcher.start()
        return {"ok": True}

    def stop_monitoring(self) -> dict[str, Any]:
        if self._watcher is not None:
            self._watcher.stop()
        return {"ok": True}

    # ----- toggles -----

    def set_dry_run(self, enabled: bool) -> dict[str, Any]:
        self._config.dry_run = bool(enabled)
        save_config(self._config, self._config_path)
        return {"ok": True}

    def set_ai_enabled(self, enabled: bool) -> dict[str, Any]:
        self._config.ai_enabled = bool(enabled)
        save_config(self._config, self._config_path)
        return {"ok": True}

    # ----- extension rules -----

    def get_extension_rules(self) -> dict[str, list[str]]:
        return self._config.categories

    def update_extension_rules(self, categories: dict[str, list[str]]) -> dict[str, Any]:
        self._config.categories = categories
        save_config(self._config, self._config_path)
        return {"ok": True}

    # ----- AI review queue -----

    def queue_for_ai_review(self, path: str) -> dict[str, Any]:
        if not self._config.ai_enabled:
            return {"ok": False, "error": "AI is disabled"}
        file_path = Path(path)
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")[:4000]
        except OSError as exc:
            return {"ok": False, "error": str(exc)}

        raw = self._ai_provider.suggest(content, file_path.name)
        result = validate_recommendation(
            raw, file_path.name, self._config.destination_folder, self._config.ai_confidence_threshold
        )
        if not result.valid:
            return {"ok": False, "error": "invalid_recommendation", "details": result.errors}

        low_confidence = result.recommendation.confidence < self._config.ai_confidence_threshold
        item = self._review_queue.add(
            file_path, result.recommendation, self._ai_provider.sends_content_externally, low_confidence
        )
        return {"ok": True, "item_id": item.id, "low_confidence": low_confidence}

    def get_review_queue(self) -> list[dict[str, Any]]:
        return [asdict(item) for item in self._review_queue.list_pending()]

    def approve_review(
        self, item_id: str, filename_override: str | None = None, destination_override: str | None = None
    ) -> dict[str, Any]:
        try:
            destination = self._review_queue.approve(
                item_id,
                self._config.destination_folder,
                self._logger,
                filename_override=filename_override,
                destination_override=destination_override,
                dry_run=self._config.dry_run,
            )
        except Exception as exc:  # noqa: BLE001 - surface any failure to the UI, never crash the app
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "destination": str(destination)}

    def reject_review(self, item_id: str) -> dict[str, Any]:
        self._review_queue.reject(item_id, self._logger)
        return {"ok": True}

    def skip_review(self, item_id: str) -> dict[str, Any]:
        self._review_queue.skip(item_id)
        return {"ok": True}

    # ----- settings -----

    def set_launch_at_login(self, enabled: bool) -> dict[str, Any]:
        self._adapter.set_launch_at_login(bool(enabled))
        self._config.launch_at_login = bool(enabled)
        save_config(self._config, self._config_path)
        return {"ok": True}

    def remove_ai_credentials(self) -> dict[str, Any]:
        self._adapter.delete_credential("ai_api_key")
        return {"ok": True}
