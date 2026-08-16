"""In-memory (persisted to disk) queue of AI recommendations awaiting human
approval. Nothing here ever moves a file without an explicit approve() call
- see docs/PRODUCT_SPEC.md section 12.
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from organizer.ai.validator import Recommendation
from organizer.core.logger import log_ai_action
from organizer.core.mover import safe_move_to


@dataclass
class ReviewItem:
    id: str
    original_path: str
    recommendation: dict  # asdict(Recommendation)
    content_left_device: bool
    low_confidence: bool


class ReviewQueue:
    def __init__(self, state_file: Path | None = None) -> None:
        self._items: dict[str, ReviewItem] = {}
        self._state_file = state_file
        if state_file is not None and state_file.exists():
            self._load()

    def add(
        self,
        original_path: Path,
        recommendation: Recommendation,
        content_left_device: bool,
        low_confidence_threshold_hit: bool = False,
    ) -> ReviewItem:
        item = ReviewItem(
            id=str(uuid.uuid4()),
            original_path=str(original_path),
            recommendation=asdict(recommendation),
            content_left_device=content_left_device,
            low_confidence=low_confidence_threshold_hit,
        )
        self._items[item.id] = item
        self._save()
        return item

    def list_pending(self) -> list[ReviewItem]:
        return list(self._items.values())

    def get(self, item_id: str) -> ReviewItem | None:
        return self._items.get(item_id)

    def skip(self, item_id: str) -> None:
        self._items.pop(item_id, None)
        self._save()

    def reject(self, item_id: str, logger: logging.Logger | None = None) -> None:
        item = self._items.pop(item_id, None)
        if item and logger:
            log_ai_action(
                logger,
                Path(item.original_path),
                Path(item.recommendation["relative_destination"]) / item.recommendation["suggested_filename"],
                item.recommendation["confidence"],
                approved=False,
            )
        self._save()

    def approve(
        self,
        item_id: str,
        destination_root: Path,
        logger: logging.Logger,
        filename_override: str | None = None,
        destination_override: str | None = None,
        dry_run: bool = False,
    ) -> Path:
        """Move the file per the (possibly user-edited) recommendation.

        Raises KeyError if item_id isn't queued, or PathSafetyError (from
        organizer.core.mover) if an override would escape destination_root -
        edits are re-validated, not trusted just because a human typed them.
        """
        item = self._items[item_id]
        filename = filename_override or item.recommendation["suggested_filename"]
        relative_dir = destination_override or item.recommendation["relative_destination"]

        destination = safe_move_to(
            Path(item.original_path), destination_root, relative_dir, filename, dry_run=dry_run
        )
        log_ai_action(logger, Path(item.original_path), destination, item.recommendation["confidence"], approved=True)

        del self._items[item_id]
        self._save()
        return destination

    def _save(self) -> None:
        if self._state_file is None:
            return
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {k: asdict(v) for k, v in self._items.items()}
        self._state_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load(self) -> None:
        try:
            data = json.loads(self._state_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        for item_id, raw in data.items():
            self._items[item_id] = ReviewItem(**raw)
