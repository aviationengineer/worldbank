"""Normalizer: raw connector dicts -> validated DataFrames."""
from __future__ import annotations

import pandas as pd
from pydantic import BaseModel

from ..utils.dates import utcnow_iso
from . import schemas


class Normalizer:
    SCHEMAS: dict[str, type[BaseModel]] = {
        "worldbank_indicators": schemas.IndicatorRecord,
        "worldbank_countries": schemas.CountryRecord,
    }

    def normalize(self, source: str, records: list[dict]) -> pd.DataFrame:
        schema = self.SCHEMAS.get(source)
        stamp = utcnow_iso()
        clean: list[dict] = []
        for rec in records:
            rec = dict(rec)
            rec.setdefault("ingestion_timestamp", stamp)
            if schema:
                try:
                    clean.append(schema(**rec).model_dump())
                except Exception:
                    continue  # malformed rows are dropped; counted in quality
            else:
                clean.append(rec)
        return pd.DataFrame(clean)
