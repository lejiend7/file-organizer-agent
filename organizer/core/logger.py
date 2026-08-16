"""Rotating activity logger. Never logs file content or credentials.

Only structured events go through here: what happened to which path, when,
and why. See docs/PRODUCT_SPEC.md section 8 and docs/ARCHITECTURE.md section 5.
"""
from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

_LOGGER_NAME = "file_organizer_agent"

# Defense in depth: even though callers should never pass content or
# credentials into a log message, reject messages that look like they
# might contain an API key/token shape, rather than trusting call sites.
_SUSPICIOUS_MARKERS = ("api_key", "apikey", "token=", "secret", "password")


class ContentScrubFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = str(record.getMessage()).lower()
        for marker in _SUSPICIOUS_MARKERS:
            if marker in msg:
                record.msg = "[redacted log message - looked like it might contain a credential]"
                record.args = ()
                break
        return True


def get_logger(log_dir: Path, max_bytes: int = 1_000_000, backup_count: int = 5) -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:
        return logger  # already configured (e.g. in tests re-requesting it)

    log_dir.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        log_dir / "activity.log", maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    handler.addFilter(ContentScrubFilter())

    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def log_moved(logger: logging.Logger, src: Path, dest: Path, dry_run: bool = False) -> None:
    prefix = "[dry-run] would move" if dry_run else "moved"
    logger.info("%s %s -> %s", prefix, src, dest)


def log_skipped(logger: logging.Logger, path: Path, reason: str) -> None:
    logger.info("skipped %s (%s)", path, reason)


def log_error(logger: logging.Logger, path: Path, error: str) -> None:
    logger.error("error processing %s: %s", path, error)


def log_ai_action(logger: logging.Logger, src: Path, dest: Path, confidence: float, approved: bool) -> None:
    action = "approved" if approved else "rejected"
    logger.info("AI suggestion %s: %s -> %s (confidence=%.2f)", action, src, dest, confidence)
