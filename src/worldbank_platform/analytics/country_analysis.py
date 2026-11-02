"""Country comparison, ranking, and latest-value summaries."""
from __future__ import annotations

import pandas as pd


def latest_values(df: pd.DataFrame, year: int | None = None) -> pd.DataFrame:
    """Latest non-null value per (country, indicator)."""
    s = df.dropna(subset=["value"]).sort_values("year")
    if year is not None:
        s = s[s["year"] <= year]
    return s.groupby(["country_code", "indicator_code"], as_index=False).last()


def compare_countries(df: pd.DataFrame, countries: list[str],
                      indicators: list[str]) -> pd.DataFrame:
    latest = latest_values(df)
    out = latest[latest["country_code"].isin(countries)
                 & latest["indicator_code"].isin(indicators)]
    return out.pivot_table(index="country_code", columns="indicator_code",
                           values="value", aggfunc="last")


def rank_countries(df: pd.DataFrame, indicator: str, year: int,
                   ascending: bool = False) -> pd.DataFrame:
    s = df[(df["indicator_code"] == indicator) & (df["year"] == year)]
    s = s.dropna(subset=["value"]).copy()
    s["rank"] = s["value"].rank(ascending=ascending, method="min").astype(int)
    return s.sort_values("rank")[["rank", "country_code", "country_name", "value"]]


def detect_outliers_iqr(df: pd.DataFrame, indicator: str) -> pd.DataFrame:
    s = df[(df["indicator_code"] == indicator)].dropna(subset=["value"]).copy()
    q1, q3 = s["value"].quantile(0.25), s["value"].quantile(0.75)
    iqr = q3 - q1
    return s[(s["value"] < q1 - 1.5 * iqr) | (s["value"] > q3 + 1.5 * iqr)]
