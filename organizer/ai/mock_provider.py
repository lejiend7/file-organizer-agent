"""A deterministic, fully local AI provider used for tests and for
AI-enabled demos without any real cloud credentials. Never sends anything
off-device.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class MockProvider:
    """Deterministic mock: proposes a mildly cleaned-up filename and files
    everything under Documents/Misc with a fixed confidence, unless
    `force_response` is set (used by tests to exercise validator edge cases).
    """

    def __init__(self, force_response: dict[str, Any] | None = None, confidence: float = 0.75) -> None:
        self._force_response = force_response
        self._confidence = confidence

    @property
    def name(self) -> str:
        return "Mock provider (local, offline)"

    @property
    def sends_content_externally(self) -> bool:
        return False

    def suggest(self, content: str, original_filename: str) -> dict[str, Any]:
        if self._force_response is not None:
            return dict(self._force_response)

        stem = Path(original_filename).stem
        suffix = "".join(Path(original_filename).suffixes) or Path(original_filename).suffix
        cleaned_stem = stem.replace("_", "-").strip("-") or "file"

        return {
            "suggested_filename": f"{cleaned_stem}{suffix}",
            "top_level_category": "Documents",
            "suggested_subfolder": "Misc",
            "confidence": self._confidence,
            "reason": "Mock provider: no real content understanding, filename lightly normalized.",
            "requires_review": True,
        }
