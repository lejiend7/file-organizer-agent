from organizer.core.config import REVIEW_FOLDER_NAME
from organizer.core.fingerprint import FingerprintCache
from organizer.core.pipeline import organize_file, scan_existing_files


def test_recognized_file_is_moved(config, logger):
    f = config.source_folder / "photo.jpg"
    f.write_text("data")
    result = organize_file(f, config, logger, skip_stability_check=True)
    assert result.outcome == "moved"
    assert result.destination == config.destination_folder / "Images" / "photo.jpg"


def test_unrecognized_file_goes_to_need_your_review(config, logger):
    f = config.source_folder / "mystery.xyz"
    f.write_text("data")
    result = organize_file(f, config, logger, skip_stability_check=True)
    assert result.outcome == "needs_review"
    assert result.destination.parent.name == REVIEW_FOLDER_NAME


def test_dry_run_leaves_file_in_place(config, logger):
    config.dry_run = True
    f = config.source_folder / "photo.jpg"
    f.write_text("data")
    result = organize_file(f, config, logger, skip_stability_check=True)
    assert result.outcome == "moved"
    assert f.exists()  # nothing actually moved
    assert not result.destination.exists()


def test_hidden_file_is_skipped(config, logger):
    f = config.source_folder / ".secret"
    f.write_text("data")
    result = organize_file(f, config, logger, skip_stability_check=True)
    assert result.outcome == "skipped"
    assert f.exists()


def test_sensitive_file_is_skipped(config, logger):
    f = config.source_folder / ".env"
    f.write_text("SECRET=1")
    result = organize_file(f, config, logger, skip_stability_check=True)
    assert result.outcome == "skipped"
    assert f.exists()


def test_missing_destination_folder_is_an_error(config, logger):
    config.destination_folder = None
    f = config.source_folder / "photo.jpg"
    f.write_text("data")
    result = organize_file(f, config, logger, skip_stability_check=True)
    assert result.outcome == "error"


def test_fingerprint_prevents_double_organizing(config, logger, tmp_path):
    cache = FingerprintCache(tmp_path / "fp.json")
    f = config.source_folder / "photo.jpg"
    f.write_text("data")

    result1 = organize_file(f, config, logger, fingerprint_cache=cache, skip_stability_check=True)
    assert result1.outcome == "moved"

    # Simulate the same file appearing again at the same (now moved-to) path
    # with an unchanged fingerprint - should be skipped, not re-moved/duplicated.
    already_organized = result1.destination
    result2 = organize_file(already_organized, config, logger, fingerprint_cache=cache, skip_stability_check=True)
    assert result2.outcome == "skipped"
    assert result2.reason == "already_organized"


def test_scan_existing_files_processes_every_file(config, logger):
    (config.source_folder / "a.jpg").write_text("1")
    (config.source_folder / "b.pdf").write_text("2")
    (config.source_folder / "c.unknownext").write_text("3")

    results = scan_existing_files(config.source_folder, config, logger)
    outcomes = {r.path.name: r.outcome for r in results}
    assert outcomes["a.jpg"] == "moved"
    assert outcomes["b.pdf"] == "moved"
    assert outcomes["c.unknownext"] == "needs_review"


def test_recursive_loop_prevention_destination_inside_source(config, logger):
    # If destination happens to be nested inside source, a file organized
    # into the destination must not immediately be picked up as a *new*
    # unorganized file in a subsequent scan of the source tree.
    nested_dest = config.source_folder / "Organized"
    nested_dest.mkdir()
    config.destination_folder = nested_dest

    f = config.source_folder / "photo.jpg"
    f.write_text("data")
    result = organize_file(f, config, logger, skip_stability_check=True)
    assert result.destination == nested_dest / "Images" / "photo.jpg"

    # scan_existing_files only iterates direct children of source_folder,
    # not recursively into the nested destination, so it won't re-catch
    # the file it just organized.
    results = scan_existing_files(config.source_folder, config, logger)
    moved_paths = {r.path for r in results}
    assert result.destination not in moved_paths
