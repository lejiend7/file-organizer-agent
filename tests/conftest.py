from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

from organizer.core.config import AppConfig


@pytest.fixture()
def tmp_source(tmp_path: Path) -> Path:
    d = tmp_path / "source"
    d.mkdir()
    return d


@pytest.fixture()
def tmp_dest(tmp_path: Path) -> Path:
    d = tmp_path / "destination"
    d.mkdir()
    return d


@pytest.fixture()
def config(tmp_source: Path, tmp_dest: Path) -> AppConfig:
    cfg = AppConfig()
    cfg.source_folder = tmp_source
    cfg.destination_folder = tmp_dest
    return cfg


@pytest.fixture()
def logger(tmp_path: Path) -> logging.Logger:
    log = logging.getLogger(f"test_{id(tmp_path)}")
    log.addHandler(logging.NullHandler())
    log.setLevel(logging.INFO)
    return log


def requires_macos(func):
    return pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only adapter test")(func)


def requires_windows(func):
    return pytest.mark.skipif(sys.platform != "win32", reason="Windows-only adapter test")(func)
