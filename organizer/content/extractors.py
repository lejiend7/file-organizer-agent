"""Minimal content extraction for the optional AI layer.

Extracts only the minimum text needed for a recommendation - never the
whole file, never binary content. Files that should never reach AI at all
(executables, keys, certs, encrypted/oversized files) are rejected here,
before any provider call, per docs/PRODUCT_SPEC.md section 9.
"""
from __future__ import annotations

from pathlib import Path

MAX_ANALYZABLE_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_EXTRACTED_CHARS = 4000

_NEVER_ANALYZE_EXTENSIONS = {
    ".exe", ".msi", ".dmg", ".pkg", ".app", ".sh", ".bat", ".cmd",
    ".pem", ".key", ".crt", ".cer", ".p12", ".pfx", ".kdbx", ".env",
}

_SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".jpg", ".jpeg", ".png", ".heic", ".tiff", ".bmp"}


class UnsupportedForAIError(Exception):
    """Raised when a file should never be sent to AI for analysis."""


def is_eligible_for_ai(path: Path, sensitive_patterns: list[str]) -> tuple[bool, str | None]:
    """Return (eligible, reason_if_not). Pure/no I/O side effects besides stat()."""
    ext = path.suffix.lower()
    if ext in _NEVER_ANALYZE_EXTENSIONS:
        return False, "excluded_file_type"
    if ext not in _SUPPORTED_EXTENSIONS:
        return False, "unsupported_file_type"
    try:
        size = path.stat().st_size
    except OSError:
        return False, "unreadable"
    if size > MAX_ANALYZABLE_BYTES:
        return False, "file_too_large"
    return True, None


def extract_text(path: Path) -> str:
    """Extract a small amount of representative text from a supported file.

    Raises UnsupportedForAIError for anything not explicitly implemented,
    rather than silently returning an empty/fake result.
    """
    ext = path.suffix.lower()

    if ext in (".txt", ".md"):
        return path.read_text(encoding="utf-8", errors="ignore")[:MAX_EXTRACTED_CHARS]

    if ext == ".pdf":
        raise NotImplementedError(
            "PDF text extraction requires the optional 'content' extra (pypdf). "
            "Install with: pip install '.[content]'"
        )

    if ext == ".docx":
        raise NotImplementedError(
            "DOCX text extraction requires the optional 'content' extra (python-docx). "
            "Install with: pip install '.[content]'"
        )

    if ext in (".jpg", ".jpeg", ".png", ".heic", ".tiff", ".bmp"):
        raise NotImplementedError(
            "Image content understanding requires a vision-capable AI provider; "
            "no local extraction is performed for images."
        )

    raise UnsupportedForAIError(f"{ext} is not eligible for AI content extraction")
