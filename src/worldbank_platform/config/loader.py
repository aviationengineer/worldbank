"""Configuration loading: YAML files + environment overrides, validated by Pydantic."""
from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from .models import AppConfig, SourceDefinition

load_dotenv()  # loads .env if present; never required

CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_config(config_dir: str | Path | None = None) -> AppConfig:
    """Load settings.yaml, sources.yaml, indicators.yaml, countries.yaml, sheets.yaml."""
    base = Path(config_dir) if config_dir else CONFIG_DIR
    settings = _read_yaml(base / "settings.yaml")
    sources_raw = _read_yaml(base / "sources.yaml").get("sources", {})
    indicators = _read_yaml(base / "indicators.yaml").get("indicators", {})
    countries = _read_yaml(base / "countries.yaml").get("countries", [])

    merged: dict = dict(settings)
    merged["countries"] = countries or merged.get("countries", [])
    merged["indicators"] = indicators
    merged["sources"] = {
        name: SourceDefinition(**spec) for name, spec in sources_raw.items()
    }

    # Environment overrides (secrets never live in YAML)
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    if sheet_id:
        merged.setdefault("sheets", {})["spreadsheet_id"] = sheet_id
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        merged.setdefault("sheets", {})["auth_mode"] = "service_account"
    base_url = os.environ.get("WB_BASE_URL")
    if base_url:
        merged.setdefault("worldbank", {})["base_url"] = base_url
    log_level = os.environ.get("WB_LOG_LEVEL")
    if log_level:
        merged.setdefault("logging", {})["level"] = log_level

    return AppConfig(**merged)
