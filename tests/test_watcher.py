import time

from organizer.core.watcher import OrganizerWatcher


def test_watcher_start_stop_lifecycle(config, logger):
    watcher = OrganizerWatcher(config, logger, poll_interval_seconds=0.1)
    assert not watcher.is_running
    watcher.start()
    assert watcher.is_running
    watcher.stop()
    assert not watcher.is_running


def test_watcher_organizes_a_dropped_file(config, logger):
    results = []
    watcher = OrganizerWatcher(config, logger, on_result=results.append, poll_interval_seconds=0.1)
    watcher.start()
    try:
        (config.source_folder / "photo.jpg").write_text("data")

        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and not results:
            time.sleep(0.1)

        assert results, "watcher did not organize the file within the timeout"
        assert results[0].outcome == "moved"
        assert (config.destination_folder / "Images" / "photo.jpg").exists()
    finally:
        watcher.stop()
