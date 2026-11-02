"""Standardizer: canonical types, codes, and dedupe keys."""
from __future__ import annotations

import pandas as pd


class Standardizer:
    DEDUPE_KEYS = {
        "worldbank_indicators": ["country_code", "indicator_code", "year"],
        "worldbank_countries": ["country_code"],
    }

    def standardize(self, source: str, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for col in ("country_code", "indicator_code", "iso2", "iso3"):
            if col in df.columns:
                df[col] = df[col].astype("string").str.strip().str.upper()
        if "year" in df.columns:
            df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        if "value" in df.columns:
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
        keys = self.DEDUPE_KEYS.get(source, [])
        if keys and all(k in df.columns for k in keys):
            df = df.drop_duplicates(subset=keys, keep="last")
        return df.reset_index(drop=True)
