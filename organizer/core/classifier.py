"""Deterministic, case-insensitive extension classification.

Never guesses. Never calls AI. A file either matches a configured extension
(including compound extensions such as ".tar.gz") or it goes to
need_your_review. See docs/PRODUCT_SPEC.md section 6.
"""
from __future__ import annotations

from pathlib import Path

from organizer.core.config import REVIEW_FOLDER_NAME


def _build_extension_index(categories: dict[str, list[str]]) -> dict[str, str]:
    """Map lowercase extension -> category, so lookups are O(1)."""
    index: dict[str, str] = {}
    for category, extensions in categories.items():
        for ext in extensions:
            index[ext.lower()] = category
    return index


def classify(filename: str, categories: dict[str, list[str]]) -> str:
    """Return the category name for `filename`, or REVIEW_FOLDER_NAME.

    Compound extensions (e.g. ".tar.gz") are checked before single
    extensions, so a file matching a longer configured suffix is not
    misclassified by its shorter suffix.
    """
    name = Path(filename).name
    if "." not in name.lstrip("."):
        return REVIEW_FOLDER_NAME

    lower = name.lower()
    index = _build_extension_index(categories)

    # Check compound extensions first (longest suffix wins), so ".tar.gz"
    # is preferred over ".gz" when both are configured.
    configured_exts = sorted(index.keys(), key=len, reverse=True)
    for ext in configured_exts:
        if lower.endswith(ext) and len(name) > len(ext):
            return index[ext]

    return REVIEW_FOLDER_NAME


def has_recognized_extension(filename: str, categories: dict[str, list[str]]) -> bool:
    return classify(filename, categories) != REVIEW_FOLDER_NAME
