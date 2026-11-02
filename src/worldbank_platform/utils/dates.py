"""Date helpers."""
from __future__ import annotations

from datetime import datetime, timezone


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_id(prefix: str = "WB") -> str:
    """Run id like WB-2026-11-01-001 (sequence per day via date stamp; uniqueness by time)."""
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    return f"{prefix}-{stamp}"


def year_range(start: int, end: int) -> list[int]:
    return list(range(start, end + 1))
