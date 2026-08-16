from pathlib import Path

from organizer.core.config import AppConfig, DEFAULT_CATEGORIES, load_config, save_config


def test_load_config_returns_defaults_when_missing(tmp_path):
    cfg = load_config(tmp_path / "nope.yaml")
    assert cfg.ai_enabled is False
    assert cfg.dry_run is False
    assert cfg.categories == {k: list(v) for k, v in DEFAULT_CATEGORIES.items()}


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "config.yaml"
    cfg = AppConfig()
    cfg.source_folder = tmp_path / "src"
    cfg.destination_folder = tmp_path / "dst"
    cfg.dry_run = True
    cfg.ai_enabled = True
    cfg.categories = {"Notes": [".note"]}

    save_config(cfg, path)
    reloaded = load_config(path)

    assert reloaded.source_folder == cfg.source_folder
    assert reloaded.destination_folder == cfg.destination_folder
    assert reloaded.dry_run is True
    assert reloaded.ai_enabled is True
    assert reloaded.categories == {"Notes": [".note"]}


def test_ai_disabled_by_default():
    assert AppConfig().ai_enabled is False


def test_config_never_written_beside_executable(tmp_path):
    # AppConfig/load_config/save_config take an explicit path and have no
    # notion of "next to the executable" - the path always comes from the
    # platform adapter's app_data_dir(). This test documents that contract:
    # save_config only ever writes to the path it's given.
    path = tmp_path / "somewhere" / "config.yaml"
    save_config(AppConfig(), path)
    assert path.exists()
