"""Trend analytics on long-format indicator data."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _series(df: pd.DataFrame, country: str, indicator: str) -> pd.DataFrame:
    s = df[(df["country_code"] == country) & (df["indicator_code"] == indicator)]
    return s.dropna(subset=["value"]).sort_values("year")


def calculate_yoy_change(df: pd.DataFrame, country: str, indicator: str) -> pd.DataFrame:
    s = _series(df, country, indicator).copy()
    s["yoy_pct"] = s["value"].pct_change(1) * 100
    return s[["year", "value", "yoy_pct"]]


def calculate_cagr(df: pd.DataFrame, country: str, indicator: str) -> float | None:
    s = _series(df, country, indicator)
    if len(s) < 2:
        return None
    first, last = float(s["value"].iloc[0]), float(s["value"].iloc[-1])
    years = int(s["year"].iloc[-1]) - int(s["year"].iloc[0])
    if first <= 0 or years <= 0:
        return None
    return (last / first) ** (1 / years) - 1


def calculate_growth_rate(df: pd.DataFrame, country: str, indicator: str,
                          start: int, end: int) -> float | None:
    s = _series(df, country, indicator)
    a = s[s["year"] == start]["value"]
    b = s[s["year"] == end]["value"]
    if a.empty or b.empty or float(a.iloc[0]) == 0:
        return None
    return (float(b.iloc[0]) - float(a.iloc[0])) / float(a.iloc[0])
