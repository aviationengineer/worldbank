"""Worksheet schemas loaded from config/sheets.yaml."""
from __future__ import annotations

from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"


def load_sheet_schemas(config_dir: str | Path | None = None) -> dict[str, list[str]]:
    base = Path(config_dir) if config_dir else CONFIG_DIR
    with open(base / "sheets.yaml", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    return raw.get("worksheets", {})


def spreadsheet_title(config_dir: str | Path | None = None) -> str:
    base = Path(config_dir) if config_dir else CONFIG_DIR
    with open(base / "sheets.yaml", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    return raw.get("spreadsheet_title", "World Bank Data Intelligence")
