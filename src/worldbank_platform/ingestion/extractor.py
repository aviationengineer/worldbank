"""Extraction engine: runs connectors, lands raw JSON, tracks state."""
from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config.models import AppConfig
from ..connectors.base import get_connector
from ..utils.dates import run_id
from .incremental import IngestMode, StateStore

log = logging.getLogger("worldbank.ingestion.extractor")


class Extractor:
    def __init__(self, config: AppConfig, raw_dir: str | Path | None = None,
                 state_path: str | Path | None = None):
        self.config = config
        self.raw_dir = Path(raw_dir or config.storage.raw_dir)
        self.states = StateStore(state_path or "metadata/ingestion_state.json")
        self.run_id = run_id()

    def _land_raw(self, source: str, endpoint: str, raw_pages: list[Any]) -> Path:
        dest = self.raw_dir / source / self.run_id
        dest.mkdir(parents=True, exist_ok=True)
        safe = endpoint.replace("/", "_")
        path = dest / f"{safe}.json"
        path.write_text(json.dumps(raw_pages, indent=1, default=str), encoding="utf-8")
        return path

    def extract(self, source_name: str, mode: str = IngestMode.FULL,
                **filters: Any) -> dict[str, Any]:
        """Run one source's connector; return summary with records + raw paths."""
        spec = self.config.sources[source_name]
        connector = get_connector(spec.connector, self.config)
        log.info("Extracting source=%s connector=%s mode=%s filters=%s",
                 source_name, spec.connector, mode, filters)
        all_records: list[dict] = []
        endpoints: list[str] = []
        for result in connector.fetch(**filters):
            all_records.extend(result.records)
            endpoints.append(result.endpoint)
            self._land_raw(source_name, result.endpoint, result.raw_pages)
        for ep in set(endpoints):
            state = self.states.get(source_name, ep)
            state.touch(record_count=len(all_records))
        self.states.save()
        log.info("Extracted source=%s records=%d", source_name, len(all_records))
        return {"source": source_name, "records": all_records,
                "endpoints": endpoints, "run_id": self.run_id}

    def extract_all(self, mode: str = IngestMode.FULL, **filters: Any) -> list[dict]:
        """Run all enabled sources; failures are isolated per source."""
        enabled = [n for n, s in self.config.sources.items() if s.enabled]
        results: list[dict] = []
        workers = max(1, self.config.http.max_workers)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            future_map = {pool.submit(self._safe_extract, n, mode, filters): n
                          for n in enabled}
            for fut in as_completed(future_map):
                results.append(fut.result())
        return results

    def _safe_extract(self, source_name: str, mode: str, filters: dict) -> dict:
        try:
            return self.extract(source_name, mode=mode, **filters)
        except Exception as exc:  # one failed source must not sink the run
            log.exception("Source %s failed", source_name)
            return {"source": source_name, "records": [],
                    "endpoints": [], "run_id": self.run_id,
                    "status": "FAILED", "error": str(exc)}
