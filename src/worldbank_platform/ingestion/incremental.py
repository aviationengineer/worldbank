"""Incremental loading state: FULL / INCREMENTAL / BACKFILL modes."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class IngestionState:
    source: str
    endpoint: str
    last_successful_run: str | None = None
    last_record_date: str | None = None
    last_page: int = 0
    record_count: int = 0
    checksum: str | None = None

    def touch(self, record_count: int = 0, last_record_date: str | None = None) -> None:
        self.last_successful_run = datetime.now(timezone.utc).isoformat()
        self.record_count = record_count
        if last_record_date:
            self.last_record_date = last_record_date


class StateStore:
    """Persists per-source state to metadata/ingestion_state.json."""

    def __init__(self, path: str | Path = "metadata/ingestion_state.json"):
        self.path = Path(path)
        self._states: dict[str, IngestionState] = {}
        self._load()

    def _key(self, source: str, endpoint: str) -> str:
        return f"{source}::{endpoint}"

    def _load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            for key, spec in raw.items():
                self._states[key] = IngestionState(**spec)

    def get(self, source: str, endpoint: str) -> IngestionState:
        key = self._key(source, endpoint)
        if key not in self._states:
            self._states[key] = IngestionState(source=source, endpoint=endpoint)
        return self._states[key]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {k: asdict(v) for k, v in self._states.items()}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class IngestMode:
    FULL = "full"
    INCREMENTAL = "incremental"
    BACKFILL = "backfill"
