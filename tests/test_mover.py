from pathlib import Path

import pytest

from organizer.core.mover import (
    PathSafetyError,
    dedupe_destination,
    ensure_within,
    is_sensitive,
    is_temp_file,
    safe_move,
    safe_move_to,
    should_ignore,
)


def _touch(path: Path, content: str = "x") -> Path:
    path.write_text(content)
    return path


def test_safe_move_creates_category_folder(tmp_source, tmp_dest):
    f = _touch(tmp_source / "photo.jpg")
    dest = safe_move(f, tmp_dest, "Images")
    assert dest == tmp_dest / "Images" / "photo.jpg"
    assert dest.exists()
    assert not f.exists()  # moved, not copied


def test_safe_move_never_overwrites_existing_file(tmp_source, tmp_dest):
    (tmp_dest / "Documents").mkdir()
    _touch(tmp_dest / "Documents" / "report.pdf", "original")

    f = _touch(tmp_source / "report.pdf", "new")
    dest = safe_move(f, tmp_dest, "Documents")

    assert dest.name == "report-2.pdf"
    assert (tmp_dest / "Documents" / "report.pdf").read_text() == "original"
    assert dest.read_text() == "new"


def test_dedupe_increments_counter(tmp_dest):
    d = tmp_dest / "Documents"
    d.mkdir()
    _touch(d / "report.pdf")
    _touch(d / "report-2.pdf")
    candidate = dedupe_destination(d, "report.pdf")
    assert candidate.name == "report-3.pdf"


def test_dedupe_preserves_compound_extension(tmp_dest):
    d = tmp_dest / "Archives"
    d.mkdir()
    _touch(d / "backup.tar.gz")
    candidate = dedupe_destination(d, "backup.tar.gz")
    assert candidate.name == "backup-2.tar.gz"


def test_dry_run_does_not_move_file(tmp_source, tmp_dest):
    f = _touch(tmp_source / "photo.jpg")
    dest = safe_move(f, tmp_dest, "Images", dry_run=True)
    assert f.exists()  # untouched
    assert not dest.exists()


def test_safe_move_rejects_escape_via_category_traversal(tmp_source, tmp_dest):
    f = _touch(tmp_source / "evil.txt")
    with pytest.raises(PathSafetyError):
        safe_move(f, tmp_dest, "../../etc")


def test_safe_move_to_rejects_traversal(tmp_source, tmp_dest):
    f = _touch(tmp_source / "evil.txt")
    with pytest.raises(PathSafetyError):
        safe_move_to(f, tmp_dest, "../outside", "evil.txt")


def test_should_ignore_directory(tmp_path):
    d = tmp_path / "subdir"
    d.mkdir()
    assert should_ignore(d, [], []) == "directory"


def test_should_ignore_hidden_file(tmp_path):
    f = _touch(tmp_path / ".hidden")
    assert should_ignore(f, [], []) == "hidden"


def test_should_ignore_ds_store(tmp_path):
    f = _touch(tmp_path / ".DS_Store")
    assert should_ignore(f, [], []) in ("ds_store", "hidden")


def test_should_ignore_sensitive_file(tmp_path):
    f = _touch(tmp_path / ".env")
    assert is_sensitive(f, [".env"])
    f2 = _touch(tmp_path / "id_rsa")
    assert is_sensitive(f2, ["id_rsa*"])


def test_should_ignore_temp_file(tmp_path):
    f = _touch(tmp_path / "download.crdownload")
    assert is_temp_file(f, [".crdownload"])
    assert should_ignore(f, [], [".crdownload"]) == "temp_file"


def test_should_ignore_symlink(tmp_path):
    target = _touch(tmp_path / "real.txt")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported in this environment")
    assert should_ignore(link, [], []) == "symlink"


def test_recognized_file_is_not_ignored(tmp_path):
    f = _touch(tmp_path / "report.pdf")
    assert should_ignore(f, [], []) is None


def test_ensure_within_raises_for_outside_path(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    with pytest.raises(PathSafetyError):
        ensure_within(base, outside)


def test_ensure_within_allows_nested_path(tmp_path):
    base = tmp_path / "base"
    nested = base / "a" / "b"
    nested.mkdir(parents=True)
    ensure_within(base, nested)  # should not raise
