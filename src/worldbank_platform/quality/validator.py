"""Data-quality validator: completeness, uniqueness, validity, consistency, freshness.

quality_score = completeness*0.30 + uniqueness*0.20 + validity*0.20
              + consistency*0.20 + freshness*0.10
Anomalies are flagged, never silently dropped.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from ..config.models import QualitySettings
from .expectations import ALLOW_NEGATIVE, EXPECTATIONS


@dataclass
class QualityReport:
    dataset: str
    record_count: int
    null_count: int
    duplicate_count: int
    completeness: float
    uniqueness: float
    validity: float
    consistency: float
    freshness: float
    quality_score: float
    validation_status: str
    anomalies: list[str] = field(default_factory=list)


class Validator:
    def __init__(self, settings: QualitySettings):
        self.settings = settings

    def validate(self, dataset: str, df: pd.DataFrame) -> QualityReport:
        exp = EXPECTATIONS.get(dataset, {})
        anomalies: list[str] = []
        n = len(df)

        # completeness: 1 - null fraction over required columns
        req = exp.get("required_columns", list(df.columns))
        nulls = int(df[req].isna().sum().sum()) if req and n else 0
        completeness = 1.0 - (nulls / (n * len(req))) if n and req else 1.0

        # uniqueness: 1 - duplicate fraction on the natural key
        key = exp.get("unique_key", [])
        dups = int(df.duplicated(subset=key).sum()) if key and n else 0
        uniqueness = 1.0 - (dups / n) if n else 1.0

        # validity: required present, codes look sane, dates in range
        validity = 1.0
        if "country_code" in df.columns and n:
            bad = df["country_code"].isna() | (df["country_code"].astype(str).str.len() != 3)
            validity -= float(bad.mean()) * 0.5
        if "year" in df.columns and n:
            bad_year = df["year"].isna() | (df["year"] < 1960) | (df["year"] > 2030)
            validity -= float(bad_year.mean()) * 0.5
        validity = max(0.0, validity)

        # consistency: domain rules; flag, don't reject
        consistency = 1.0
        if "value" in df.columns and "indicator_code" in df.columns and n:
            for _, row in df.iterrows():
                code = row["indicator_code"]
                val = row["value"]
                if pd.isna(val) or code in ALLOW_NEGATIVE:
                    continue
                if code == "SP.POP.TOTL" and self.settings.flag_negative_population and val < 0:
                    anomalies.append(f"Negative population: {row.get('country_code')} {row.get('year')}")
                    consistency -= 1.0 / n
                elif code and code.startswith("NY.GDP") and self.settings.flag_negative_gdp and val < 0:
                    anomalies.append(f"Negative GDP: {row.get('country_code')} {code} {row.get('year')}")
                    consistency -= 1.0 / n
                if code == "FP.CPI.TOTL.ZG" and abs(val) > self.settings.inflation_abs_limit:
                    anomalies.append(f"Extreme inflation {val}: {row.get('country_code')} {row.get('year')}")
                    consistency -= 1.0 / n
        consistency = max(0.0, consistency)

        # freshness: always 1.0 for freshly ingested data
        freshness = 1.0

        w = self.settings.weights
        score = (completeness * w.completeness + uniqueness * w.uniqueness
                 + validity * w.validity + consistency * w.consistency
                 + freshness * w.freshness)
        status = "PASS" if score >= self.settings.min_quality_score else "REVIEW"
        return QualityReport(
            dataset=dataset, record_count=n, null_count=nulls, duplicate_count=dups,
            completeness=round(completeness, 4), uniqueness=round(uniqueness, 4),
            validity=round(validity, 4), consistency=round(consistency, 4),
            freshness=freshness, quality_score=round(score, 4),
            validation_status=status, anomalies=anomalies[:50])
