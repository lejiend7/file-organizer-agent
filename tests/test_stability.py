import time

from organizer.core.stability import StabilityTracker, wait_until_stable


def test_stability_tracker_reports_stable_after_n_consistent_observations(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("hello")
    tracker = StabilityTracker(checks=2)

    assert tracker.observe(f) is False  # first observation, count=1
    assert tracker.observe(f) is True  # second observation, same size/mtime, count=2


def test_stability_tracker_resets_on_change(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("hello")
    tracker = StabilityTracker(checks=2)
    tracker.observe(f)

    time.sleep(0.05)
    f.write_text("hello world, now bigger")
    assert tracker.observe(f) is False  # changed, count resets to 1


def test_stability_tracker_handles_missing_file(tmp_path):
    tracker = StabilityTracker(checks=2)
    assert tracker.observe(tmp_path / "nonexistent.txt") is False


def test_wait_until_stable_returns_true_for_static_file(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("hello")
    assert wait_until_stable(f, checks=2, interval_seconds=0.05, timeout_seconds=1.0) is True


def test_wait_until_stable_returns_false_for_missing_file(tmp_path):
    assert wait_until_stable(tmp_path / "gone.txt", timeout_seconds=0.2, interval_seconds=0.05) is False
