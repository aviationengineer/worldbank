"""Dataset profiler: counts, nulls, distributions, ranges."""
from __future__ import annotations

import pandas as pd


def profile(df: pd.DataFrame) -> dict:
    numeric = df.select_dtypes(include="number")
    out: dict = {
        "record_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "null_percentage": round(float(df.isna().mean().mean() * 100), 2),
        "columns": {},
    }
    for col in df.columns:
        s = df[col]
        info: dict = {"null_pct": round(float(s.isna().mean() * 100), 2),
                      "unique": int(s.nunique(dropna=True))}
        if col in numeric.columns:
            info.update({
                "min": float(s.min()), "max": float(s.max()),
                "mean": round(float(s.mean()), 4), "median": float(s.median()),
                "std": round(float(s.std()), 4)})
        out["columns"][col] = info
    if "year" in df.columns:
        out["year_min"] = int(df["year"].min())
        out["year_max"] = int(df["year"].max())
    if "country_code" in df.columns:
        out["country_count"] = int(df["country_code"].nunique())
    if "indicator_code" in df.columns:
        out["indicator_count"] = int(df["indicator_code"].nunique())
    return out
