from pathlib import Path

import pytest

from organizer.ai.validator import validate_recommendation
from organizer.core.mover import PathSafetyError
from organizer.review.queue import ReviewQueue

RAW = {
    "suggested_filename": "AWS-Invoice-2026-08.pdf",
    "top_level_category": "Documents",
    "suggested_subfolder": "Finance/Invoices",
    "confidence": 0.94,
    "reason": "Looks like an AWS invoice.",
    "requires_review": True,
}


def _queued_item(tmp_source, tmp_dest, filename="invoice_scan_001.pdf", raw=None):
    src = tmp_source / filename
    src.write_text("pdf-ish content")
    result = validate_recommendation(raw or RAW, filename, tmp_dest)
    assert result.valid
    return src, result.recommendation


def test_approve_moves_the_file(tmp_source, tmp_dest, logger):
    src, rec = _queued_item(tmp_source, tmp_dest)
    queue = ReviewQueue()
    item = queue.add(src, rec, content_left_device=False)

    destination = queue.approve(item.id, tmp_dest, logger)
    assert destination == tmp_dest / "Documents" / "Finance" / "Invoices" / "AWS-Invoice-2026-08.pdf"
    assert destination.exists()
    assert not src.exists()
    assert queue.get(item.id) is None


def test_reject_does_not_move_file(tmp_source, tmp_dest, logger):
    src, rec = _queued_item(tmp_source, tmp_dest)
    queue = ReviewQueue()
    item = queue.add(src, rec, content_left_device=False)

    queue.reject(item.id, logger)
    assert src.exists()
    assert queue.get(item.id) is None


def test_skip_leaves_item_untouched_on_disk(tmp_source, tmp_dest):
    src, rec = _queued_item(tmp_source, tmp_dest)
    queue = ReviewQueue()
    item = queue.add(src, rec, content_left_device=False)

    queue.skip(item.id)
    assert src.exists()
    assert queue.get(item.id) is None


def test_approve_with_edited_filename_and_destination(tmp_source, tmp_dest, logger):
    src, rec = _queued_item(tmp_source, tmp_dest)
    queue = ReviewQueue()
    item = queue.add(src, rec, content_left_device=False)

    destination = queue.approve(
        item.id, tmp_dest, logger, filename_override="Renamed-Invoice.pdf", destination_override="Documents"
    )
    assert destination == tmp_dest / "Documents" / "Renamed-Invoice.pdf"


def test_approve_rejects_edited_destination_that_escapes_root(tmp_source, tmp_dest, logger):
    src, rec = _queued_item(tmp_source, tmp_dest)
    queue = ReviewQueue()
    item = queue.add(src, rec, content_left_device=False)

    with pytest.raises(PathSafetyError):
        queue.approve(item.id, tmp_dest, logger, destination_override="../../etc")


def test_dry_run_approve_does_not_move_file(tmp_source, tmp_dest, logger):
    src, rec = _queued_item(tmp_source, tmp_dest)
    queue = ReviewQueue()
    item = queue.add(src, rec, content_left_device=False)

    destination = queue.approve(item.id, tmp_dest, logger, dry_run=True)
    assert src.exists()
    assert not destination.exists()


def test_state_persists_across_instances(tmp_source, tmp_dest, tmp_path):
    state_file = tmp_path / "queue.json"
    src, rec = _queued_item(tmp_source, tmp_dest)

    queue = ReviewQueue(state_file)
    item = queue.add(src, rec, content_left_device=True, low_confidence_threshold_hit=False)

    reloaded = ReviewQueue(state_file)
    reloaded_item = reloaded.get(item.id)
    assert reloaded_item is not None
    assert reloaded_item.content_left_device is True
