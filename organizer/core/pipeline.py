"""Ties classifier + stability + mover + fingerprint + logger together.

This is the single organizing pipeline both the live watcher and a one-off
"scan existing files" pass call into, and what tests exercise directly
without needing a real watchdog Observer thread running.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from organizer.core.config import REVIEW_FOLDER_NAME, AppConfig
from organizer.core.classifier import classify
from organizer.core.fingerprint import FingerprintCache
from organizer.core.logger import log_error, log_moved, log_skipped
from organizer.core.mover import PathSafetyError, safe_move, should_ignore
from organizer.core.stability import StabilityTracker


@dataclass
class OrganizeResult:
    path: Path
    outcome: str  # "moved", "skipped", "pending_stability", "error"
    destination: Path | None = None
    reason: str | None = None


def organize_file(
    path: Path,
    config: AppConfig,
    logger: logging.Logger,
    fingerprint_cache: FingerprintCache | None = None,
    stability: StabilityTracker | None = None,
    skip_stability_check: bool = False,
) -> OrganizeResult:
    """Run one file through the organizing pipeline.

    Safe to call repeatedly on the same path (e.g. from multiple watcher
    events) - the fingerprint cache and stability tracker make repeat calls
    idempotent rather than re-moving or re-logging the same file.
    """
    if config.destination_folder is None:
        return OrganizeResult(path, "error", reason="no destination folder configured")

    if not path.exists():
        return OrganizeResult(path, "skipped", reason="no_longer_exists")

    ignore_reason = should_ignore(path, config.sensitive_patterns, config.temp_extensions)
    if ignore_reason:
        log_skipped(logger, path, ignore_reason)
        return OrganizeResult(path, "skipped", reason=ignore_reason)

    if fingerprint_cache is not None and fingerprint_cache.is_unchanged(path):
        return OrganizeResult(path, "skipped", reason="already_organized")

    if not skip_stability_check:
        tracker = stability or StabilityTracker()
        if not tracker.observe(path):
            return OrganizeResult(path, "pending_stability", reason="waiting_for_file_to_settle")

    category = classify(path.name, config.categories)

    try:
        destination = safe_move(path, config.destination_folder, category, dry_run=config.dry_run)
    except PathSafetyError as exc:
        log_error(logger, path, str(exc))
        return OrganizeResult(path, "error", reason=str(exc))
    except OSError as exc:
        log_error(logger, path, str(exc))
        return OrganizeResult(path, "error", reason=str(exc))

    log_moved(logger, path, destination, dry_run=config.dry_run)

    if fingerprint_cache is not None and not config.dry_run:
        fingerprint_cache.record(destination)
        fingerprint_cache.save()

    outcome = "moved" if category != REVIEW_FOLDER_NAME else "needs_review"
    return OrganizeResult(path, outcome, destination=destination)


def scan_existing_files(
    source_folder: Path,
    config: AppConfig,
    logger: logging.Logger,
    fingerprint_cache: FingerprintCache | None = None,
) -> list[OrganizeResult]:
    """One-off pass over files already sitting in the source folder.

    Skips the stability wait (files already at rest don't need it) but
    still runs every other safety check.
    """
    results = []
    for entry in sorted(source_folder.iterdir()):
        if entry.is_dir():
            continue
        results.append(
            organize_file(entry, config, logger, fingerprint_cache=fingerprint_cache, skip_stability_check=True)
        )
    return results
