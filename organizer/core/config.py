"""Configuration loading/saving for the shared core.

This module never knows *where* the config file lives on a given OS -
that path comes from the platform adapter (see organizer/platforms/base.py)
and is passed in explicitly. Keeping the path resolution out of this module
is what lets organizer/core stay platform-agnostic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CATEGORIES: dict[str, list[str]] = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".heic", ".tiff", ".bmp"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".pages", ".epub"],
    "Spreadsheets": [".csv", ".xls", ".xlsx", ".numbers", ".ods"],
    "Presentations": [".ppt", ".pptx", ".key", ".odp"],
    "Videos": [".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"],
    "Audio": [".mp3", ".wav", ".aac", ".m4a", ".flac", ".ogg"],
    "Archives": [".zip", ".rar", ".7z", ".tar.gz", ".tar", ".gz", ".bz2"],
    "Code": [
        ".js", ".jsx", ".ts", ".tsx", ".py", ".java", ".php", ".html", ".css",
        ".scss", ".json", ".xml", ".yaml", ".yml", ".sh", ".sql", ".go", ".rs", ".swift",
    ],
    "Installers": [".dmg", ".pkg", ".exe", ".msi"],
}

DEFAULT_SENSITIVE_PATTERNS: list[str] = [
    ".env", "*.pem", "*.key", "*.crt", "*.cer", "*.p12", "*.pfx", "id_rsa*", "*.kdbx",
]

DEFAULT_TEMP_EXTENSIONS: list[str] = [".crdownload", ".download", ".part", ".tmp"]

REVIEW_FOLDER_NAME = "need_your_review"


@dataclass
class AppConfig:
    source_folder: Path | None = None
    destination_folder: Path | None = None
    dry_run: bool = False
    ai_enabled: bool = False
    ai_confidence_threshold: float = 0.6
    categories: dict[str, list[str]] = field(default_factory=lambda: {k: list(v) for k, v in DEFAULT_CATEGORIES.items()})
    sensitive_patterns: list[str] = field(default_factory=lambda: list(DEFAULT_SENSITIVE_PATTERNS))
    temp_extensions: list[str] = field(default_factory=lambda: list(DEFAULT_TEMP_EXTENSIONS))
    launch_at_login: bool = False
    telemetry_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_folder": str(self.source_folder) if self.source_folder else None,
            "destination_folder": str(self.destination_folder) if self.destination_folder else None,
            "dry_run": self.dry_run,
            "ai_enabled": self.ai_enabled,
            "ai_confidence_threshold": self.ai_confidence_threshold,
            "categories": self.categories,
            "sensitive_patterns": self.sensitive_patterns,
            "temp_extensions": self.temp_extensions,
            "launch_at_login": self.launch_at_login,
            "telemetry_enabled": self.telemetry_enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        source = data.get("source_folder")
        dest = data.get("destination_folder")
        return cls(
            source_folder=Path(source) if source else None,
            destination_folder=Path(dest) if dest else None,
            dry_run=bool(data.get("dry_run", False)),
            ai_enabled=bool(data.get("ai_enabled", False)),
            ai_confidence_threshold=float(data.get("ai_confidence_threshold", 0.6)),
            categories=data.get("categories") or {k: list(v) for k, v in DEFAULT_CATEGORIES.items()},
            sensitive_patterns=data.get("sensitive_patterns") or list(DEFAULT_SENSITIVE_PATTERNS),
            temp_extensions=data.get("temp_extensions") or list(DEFAULT_TEMP_EXTENSIONS),
            launch_at_login=bool(data.get("launch_at_login", False)),
            telemetry_enabled=bool(data.get("telemetry_enabled", False)),
        )


def default_config() -> AppConfig:
    return AppConfig()


def load_config(path: Path) -> AppConfig:
    """Load config from `path`. Returns defaults if the file doesn't exist yet."""
    if not path.exists():
        return default_config()
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return AppConfig.from_dict(data)


def save_config(config: AppConfig, path: Path) -> None:
    """Save config to `path`, creating parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config.to_dict(), f, sort_keys=False)
