"""Analytics-layer profiling (wraps quality.profiler with narrative)."""
from __future__ import annotations

import pandas as pd

from ..quality.profiler import profile


def dataset_summary(df: pd.DataFrame, name: str) -> dict:
    summary = profile(df)
    summary["dataset"] = name
    return summary


def natural_language_summary(df: pd.DataFrame, country: str, country_name: str,
                             indicator: str, indicator_name: str) -> str:
    """'Canada GDP increased by X% between 2000 and 2024.' — from validated data only."""
    from .trends import calculate_growth_rate
    s = df[(df["country_code"] == country) & (df["indicator_code"] == indicator)]
    s = s.dropna(subset=["value"]).sort_values("year")
    if len(s) < 2:
        return f"Insufficient validated data for {indicator_name} in {country_name}."
    y0, y1 = int(s["year"].iloc[0]), int(s["year"].iloc[-1])
    g = calculate_growth_rate(df, country, indicator, y0, y1)
    if g is None:
        return f"Insufficient validated data for {indicator_name} in {country_name}."
    direction = "increased" if g >= 0 else "decreased"
    return (f"{country_name} {indicator_name} {direction} by {abs(g)*100:.1f}% "
            f"between {y0} and {y1}.")
