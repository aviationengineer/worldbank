"""Audit log: one JSON record per pipeline run."""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("worldbank.audit")


@dataclass
class AuditRecord:
    run_id: str
    pipeline: str = "worldbank-ingest"
    source: str = ""
    endpoint: str = ""
    start_time: str = ""
    end_time: str = ""
    status: str = "RUNNING"
    records_read: int = 0
    records_written: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class AuditLog:
    def __init__(self, path: str | Path = "logs/audit.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, record: AuditRecord) -> None:
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(record), default=str) + "\n")
        log.info("audit run_id=%s status=%s read=%d written=%d",
                 record.run_id, record.status, record.records_read, record.records_written)

    @staticmethod
    def start(run_id: str, source: str, endpoint: str = "") -> AuditRecord:
        now = datetime.now(timezone.utc).isoformat()
        return AuditRecord(run_id=run_id, source=source, endpoint=endpoint, start_time=now)
