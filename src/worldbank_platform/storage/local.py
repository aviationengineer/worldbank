"""Local filesystem layout: data/raw, data/processed, data/analytics."""
from __future__ import annotations

from pathlib import Path

from ..config.models import StorageSettings


class LocalStore:
    def __init__(self, settings: StorageSettings):
        self.settings = settings
        for d in (settings.raw_dir, settings.processed_dir, settings.analytics_dir):
            Path(d).mkdir(parents=True, exist_ok=True)

    def processed_path(self, dataset: str, run_id: str, fmt: str = "parquet") -> Path:
        dest = Path(self.settings.processed_dir) / dataset
        dest.mkdir(parents=True, exist_ok=True)
        return dest / f"{run_id}.{fmt}"

    def analytics_path(self, name: str, fmt: str = "parquet") -> Path:
        dest = Path(self.settings.analytics_dir)
        dest.mkdir(parents=True, exist_ok=True)
        return dest / f"{name}.{fmt}"
