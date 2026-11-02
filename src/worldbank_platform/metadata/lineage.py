"""Dataset lineage records: source -> endpoint -> transforms -> destination."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from ..utils.dates import utcnow_iso


@dataclass
class LineageRecord:
    dataset: str
    source_api: str
    endpoint: str
    extraction_timestamp: str
    transformation: str
    destination: str

    def as_dict(self) -> dict:
        return asdict(self)


class LineageTracker:
    """In-memory tracker that also persists to logs/lineage.jsonl so separate
    CLI invocations (ingest vs publish) share lineage."""

    def __init__(self, path: str | Path = "logs/lineage.jsonl"):
        self.path = Path(path)
        self.records: list[LineageRecord] = []
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                try:
                    self.records.append(LineageRecord(**json.loads(line)))
                except (ValueError, TypeError):
                    continue

    def add(self, dataset: str, source_api: str, endpoint: str,
            transformation: str, destination: str) -> LineageRecord:
        rec = LineageRecord(dataset=dataset, source_api=source_api, endpoint=endpoint,
                            extraction_timestamp=utcnow_iso(),
                            transformation=transformation, destination=destination)
        self.records.append(rec)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec.as_dict()) + "\n")
        return rec

    def rows(self) -> list[dict]:
        return [r.as_dict() for r in self.records]
