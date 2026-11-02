"""Pipeline orchestrator: extract -> normalize -> standardize -> quality -> store."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from .config.loader import load_config
from .config.models import AppConfig
from .google_sheets.client import make_transport
from .google_sheets.formatter import format_dataframe
from .google_sheets.schema import load_sheet_schemas, spreadsheet_title
from .google_sheets.writer import GoogleSheetsWriter
from .ingestion.extractor import Extractor
from .ingestion.incremental import IngestMode
from .metadata.audit import AuditLog, AuditRecord
from .metadata.catalog import Catalog
from .metadata.lineage import LineageTracker
from .quality.profiler import profile
from .quality.validator import QualityReport, Validator
from .storage.local import LocalStore
from .storage.parquet import read_parquet, write_parquet
from .transformation.normalizer import Normalizer
from .transformation.standardizer import Standardizer
from .utils.dates import utcnow_iso
from .utils.logging import get_logger

log = get_logger("worldbank.pipeline")


class Pipeline:
    def __init__(self, config: AppConfig | None = None):
        self.config = config or load_config()
        self.extractor = Extractor(self.config)
        self.normalizer = Normalizer()
        self.standardizer = Standardizer()
        self.validator = Validator(self.config.quality)
        self.store = LocalStore(self.config.storage)
        self.audit = AuditLog()
        self.lineage = LineageTracker()
        self.catalog = Catalog(self.config)

    # -- ingest -----------------------------------------------------------
    def run_source(self, source: str, mode: str = IngestMode.FULL,
                   **filters: Any) -> dict[str, Any]:
        run_id = self.extractor.run_id
        audit_rec = AuditLog.start(run_id, source)
        try:
            extracted = self.extractor.extract(source, mode=mode, **filters)
            records = extracted["records"]
            audit_rec.records_read = len(records)

            df = self.normalizer.normalize(source, records)
            df = self.standardizer.standardize(source, df)
            report = self.validator.validate(source, df)

            pq_path = self.store.processed_path(source, run_id)
            write_parquet(df, pq_path)
            audit_rec.records_written = len(df)

            for ep in extracted["endpoints"]:
                self.lineage.add(dataset=source, source_api="World Bank",
                                 endpoint=ep, transformation="normalize+standardize+validate",
                                 destination=f"parquet:{pq_path}")
            audit_rec.status = "SUCCESS" if report.validation_status == "PASS" else "SUCCESS_WITH_WARNINGS"
            audit_rec.warnings = report.anomalies
            summary = {"run_id": run_id, "source": source, "records": len(df),
                       "quality": report, "profile": profile(df),
                       "parquet": str(pq_path), "status": audit_rec.status}
        except Exception as exc:
            log.exception("Pipeline failed for %s", source)
            audit_rec.status = "FAILED"
            audit_rec.errors = [str(exc)]
            summary = {"run_id": run_id, "source": source, "records": 0,
                       "status": "FAILED", "error": str(exc)}
        finally:
            audit_rec.end_time = utcnow_iso()
            self.audit.write(audit_rec)
        return summary

    def run_all(self, mode: str = IngestMode.FULL, **filters: Any) -> list[dict]:
        return [self.run_source(name, mode=mode, **filters)
                for name, spec in self.config.sources.items() if spec.enabled]

    # -- publish ----------------------------------------------------------
    def latest_parquet(self, dataset: str) -> Path | None:
        d = Path(self.config.storage.processed_dir) / dataset
        if not d.exists():
            return None
        files = sorted(d.glob("*.parquet"))
        return files[-1] if files else None

    def publish_sheets(self, spreadsheet_id: str | None = None,
                       datasets: list[str] | None = None) -> dict[str, Any]:
        sid = spreadsheet_id or self.config.sheets.spreadsheet_id
        if not sid:
            raise RuntimeError("No spreadsheet id: set GOOGLE_SHEET_ID or sheets.spreadsheet_id")
        transport = make_transport(self.config.sheets.auth_mode)
        writer = GoogleSheetsWriter(transport, sid)
        schemas = load_sheet_schemas()
        published: dict[str, int] = {}

        def _publish(sheet: str, df: pd.DataFrame) -> None:
            cols = schemas.get(sheet)
            if cols:
                df = df.reindex(columns=cols)
            writer.write_dataframe(sheet, format_dataframe(df))
            writer.format_header(sheet, len(df.columns))
            published[sheet] = len(df)

        # curated datasets
        for dataset in (datasets or ["worldbank_indicators", "worldbank_countries"]):
            pq = self.latest_parquet(dataset)
            if pq is None:
                continue
            df = read_parquet(pq)
            sheet = "04_Indicators" if dataset == "worldbank_indicators" else "02_Country"
            _publish(sheet, df)

        # reference / ops sheets
        _publish("01_Source_Catalog", pd.DataFrame(self.catalog.source_rows()))
        _publish("06_Datasets", pd.DataFrame(self.catalog.dataset_rows()))
        _publish("09_Data_Lineage", pd.DataFrame(self.lineage.rows()))
        _publish("03_Indicator_Catalog", pd.DataFrame(
            [{"indicator_code": c, "indicator_name": m.get("name"),
              "description": m.get("name"), "unit": m.get("unit"),
              "source": "World Bank", "source_organization": "World Bank",
              "topic": m.get("topic")}
             for c, m in self.config.indicators.items()]))
        for empty in ("05_Projects",):
            cols = schemas.get(empty, [])
            writer.write_dataframe(empty, pd.DataFrame(columns=cols))
            published[empty] = 0
        # analytics summary: latest key metrics per country
        analytics_df = self._analytics_summary()
        if not analytics_df.empty:
            _publish("10_Analytics", analytics_df)
        else:
            cols = schemas.get("10_Analytics", [])
            writer.write_dataframe("10_Analytics", pd.DataFrame(columns=cols))
            published["10_Analytics"] = 0
        # real ops data: quality re-computed on latest curated data, audit log rows
        q_rows, log_rows = self._ops_rows(datasets or ["worldbank_indicators",
                                                       "worldbank_countries"])
        if q_rows:
            _publish("07_Data_Quality", pd.DataFrame(q_rows))
        if log_rows:
            _publish("08_Ingestion_Log", pd.DataFrame(log_rows))
        return {"spreadsheet_id": sid, "published": published}

    def _analytics_summary(self) -> "pd.DataFrame":
        """Latest GDP / growth / population / inflation / unemployment / GDP p.c.
        per country present in the curated indicators."""
        import pandas as _pd
        from .analytics.country_analysis import latest_values
        pq = self.latest_parquet("worldbank_indicators")
        if pq is None:
            return _pd.DataFrame()
        latest = latest_values(read_parquet(pq))
        cols = {"NY.GDP.MKTP.CD": "gdp", "NY.GDP.MKTP.KD.ZG": "gdp_growth",
                "SP.POP.TOTL": "population", "FP.CPI.TOTL.ZG": "inflation",
                "SL.UEM.TOTL.ZS": "unemployment", "NY.GDP.PCAP.CD": "gdp_per_capita"}
        sub = latest[latest["indicator_code"].isin(cols)]
        if sub.empty:
            return _pd.DataFrame()
        piv = sub.pivot_table(index=["country_code", "country_name"],
                              columns="indicator_code", values="value", aggfunc="last")
        piv = piv.rename(columns=cols).reset_index()
        piv = piv.rename(columns={"country_code": "country"})
        return piv[["country"] + [c for c in cols.values() if c in piv.columns]]

    def _ops_rows(self, datasets: list[str]) -> tuple[list[dict], list[dict]]:
        """Data-quality rows (recomputed) + ingestion-log rows (from audit log)."""
        q_rows: list[dict] = []
        for dataset in datasets:
            pq = self.latest_parquet(dataset)
            if pq is None:
                continue
            report = self.validator.validate(dataset, read_parquet(pq))
            q_rows.append({
                "run_id": pq.stem, "dataset": dataset,
                "record_count": report.record_count, "null_count": report.null_count,
                "duplicate_count": report.duplicate_count,
                "quality_score": report.quality_score,
                "validation_status": report.validation_status,
                "run_timestamp": utcnow_iso()})
        log_rows: list[dict] = []
        audit_path = __import__("pathlib").Path("logs/audit.jsonl")
        if audit_path.exists():
            import json as _json
            for line in audit_path.read_text(encoding="utf-8").splitlines()[-50:]:
                try:
                    r = _json.loads(line)
                except ValueError:
                    continue
                log_rows.append({
                    "run_id": r.get("run_id"), "source": r.get("source"),
                    "endpoint": r.get("endpoint"), "start_time": r.get("start_time"),
                    "end_time": r.get("end_time"),
                    "records_extracted": r.get("records_read"),
                    "records_loaded": r.get("records_written"),
                    "status": r.get("status"),
                    "error_message": "; ".join(r.get("errors", []))})
        return q_rows, log_rows

    def ensure_spreadsheet(self, title: str | None = None) -> str:
        transport = make_transport(self.config.sheets.auth_mode)
        writer = GoogleSheetsWriter(transport, self.config.sheets.spreadsheet_id)
        sid = writer.create_spreadsheet(title or spreadsheet_title())
        for sheet in load_sheet_schemas():
            writer.create_worksheet(sheet)
        return sid
