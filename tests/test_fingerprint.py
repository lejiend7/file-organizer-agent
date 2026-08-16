from organizer.core.fingerprint import FingerprintCache, compute_fingerprint


def test_compute_fingerprint_changes_when_content_changes(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("version 1")
    fp1 = compute_fingerprint(f)

    f.write_text("version 2 - quite different content")
    fp2 = compute_fingerprint(f)

    assert fp1 != fp2


def test_compute_fingerprint_none_for_missing_file(tmp_path):
    assert compute_fingerprint(tmp_path / "missing.txt") is None


def test_cache_round_trip(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("hello")
    cache_file = tmp_path / "cache.json"

    cache = FingerprintCache(cache_file)
    assert cache.is_unchanged(f) is False

    cache.record(f)
    cache.save()

    reloaded = FingerprintCache(cache_file)
    assert reloaded.is_unchanged(f) is True


def test_cache_detects_change_after_record(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("hello")
    cache = FingerprintCache(tmp_path / "cache.json")
    cache.record(f)

    f.write_text("hello, but now edited with more text")
    assert cache.is_unchanged(f) is False
