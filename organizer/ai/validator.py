"""Validates raw AI provider output before it can touch the filesystem.

This is the single gate between AI output and any file move -
docs/ARCHITECTURE.md section 5 calls this out as the one piece of code
written defensively against a hostile/malformed provider, because AI
output is untrusted input by definition (docs/PRODUCT_SPEC.md section 11).

Nothing outside this module should ever act on raw provider output.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

MAX_FILENAME_LENGTH = 200
MAX_PATH_COMPONENT_LENGTH = 100

# Reserved on Windows; rejected everywhere so a recommendation is safe on
# both platforms regardless of which OS approves it (docs/PRODUCT_SPEC.md section 13).
_WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

# Rejected in filenames on at least one supported platform.
_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

_REQUIRED_FIELDS = {
    "suggested_filename": str,
    "top_level_category": str,
    "suggested_subfolder": str,
    "confidence": (int, float),
    "reason": str,
    "requires_review": bool,
}


@dataclass
class Recommendation:
    suggested_filename: str
    top_level_category: str
    suggested_subfolder: str
    confidence: float
    reason: str
    requires_review: bool
    relative_destination: str  # top_level_category/suggested_subfolder, safe to join


@dataclass
class ValidationResult:
    valid: bool
    recommendation: Recommendation | None
    errors: list[str]


def _has_valid_shape(raw: dict, errors: list[str]) -> bool:
    if not isinstance(raw, dict):
        errors.append("response is not a JSON object")
        return False
    ok = True
    for field, expected_type in _REQUIRED_FIELDS.items():
        if field not in raw:
            errors.append(f"missing field: {field}")
            ok = False
        elif not isinstance(raw[field], expected_type):
            errors.append(f"field {field} has wrong type")
            ok = False
    return ok


def _is_safe_path_component(component: str) -> bool:
    if not component or component in (".", ".."):
        return False
    if len(component) > MAX_PATH_COMPONENT_LENGTH:
        return False
    if _INVALID_FILENAME_CHARS.search(component):
        return False
    name_without_ext = component.split(".")[0].upper()
    if name_without_ext in _WINDOWS_RESERVED_NAMES:
        return False
    if component.endswith(".") or component.endswith(" "):
        return False
    return True


def validate_recommendation(
    raw: dict,
    original_filename: str,
    destination_root: Path,
    confidence_threshold: float = 0.6,
) -> ValidationResult:
    """Validate a raw provider response against the contract in
    docs/PRODUCT_SPEC.md section 11. Returns valid=False (never raises) for
    any malformed, unsafe, or low-confidence response - callers should leave
    such files in need_your_review rather than surface them for approval.
    """
    errors: list[str] = []

    if not _has_valid_shape(raw, errors):
        return ValidationResult(False, None, errors)

    filename = raw["suggested_filename"].strip()
    category = raw["top_level_category"].strip()
    subfolder = raw["suggested_subfolder"].strip().strip("/\\")
    confidence = float(raw["confidence"])
    reason = raw["reason"].strip()
    requires_review = bool(raw["requires_review"])

    original_ext = "".join(Path(original_filename).suffixes) or Path(original_filename).suffix
    if original_ext and not filename.lower().endswith(original_ext.lower()):
        errors.append("suggested_filename does not preserve the original extension")

    if not (0.0 <= confidence <= 1.0):
        errors.append("confidence out of range 0..1")

    if len(filename) > MAX_FILENAME_LENGTH:
        errors.append("suggested_filename too long")

    if Path(filename).is_absolute():
        errors.append("suggested_filename must not be an absolute path")
    if ".." in Path(filename).parts:
        errors.append("suggested_filename contains path traversal")
    if not _is_safe_path_component(filename):
        errors.append("suggested_filename is not a safe filename")

    subfolder_parts = [p for p in re.split(r"[\\/]", subfolder) if p]
    if any(p == ".." for p in subfolder_parts):
        errors.append("suggested_subfolder contains path traversal")
    for part in [category, *subfolder_parts]:
        if not _is_safe_path_component(part):
            errors.append(f"unsafe path component: {part!r}")

    if not reason:
        errors.append("reason must not be empty")

    if errors:
        return ValidationResult(False, None, errors)

    relative_destination = str(Path(category, *subfolder_parts))

    # Path must resolve inside destination_root even after joining - defense
    # in depth beyond the component-level checks above.
    candidate_dir = (destination_root / relative_destination).resolve()
    try:
        root_resolved = destination_root.resolve()
    except OSError:
        errors.append("destination_root does not resolve")
        return ValidationResult(False, None, errors)
    if candidate_dir != root_resolved and root_resolved not in candidate_dir.parents:
        errors.append("resolved destination escapes destination_root")
        return ValidationResult(False, None, errors)

    if (candidate_dir / filename).exists():
        errors.append("a file already exists at the proposed destination")
        return ValidationResult(False, None, errors)

    if confidence < confidence_threshold:
        requires_review = True

    recommendation = Recommendation(
        suggested_filename=filename,
        top_level_category=category,
        suggested_subfolder=subfolder,
        confidence=confidence,
        reason=reason,
        requires_review=requires_review,
        relative_destination=relative_destination,
    )

    # Low-confidence recommendations are structurally valid but the caller
    # (review queue) must not offer them as one-click approvable - it should
    # route them back to need_your_review instead. We signal this by keeping
    # valid=True (the JSON itself is fine) while requires_review stays True;
    # UI-layer policy in organizer/review/queue.py decides what to do with it.
    return ValidationResult(True, recommendation, errors)
