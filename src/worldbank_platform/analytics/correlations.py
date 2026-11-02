"""Cross-indicator correlations."""
from __future__ import annotations

import pandas as pd


def wide(df: pd.DataFrame, country: str) -> pd.DataFrame:
    s = df[df["country_code"] == country]
    return s.pivot_table(index="year", columns="indicator_code",
                         values="value", aggfunc="last")


def calculate_indicator_correlation(df: pd.DataFrame, country: str) -> pd.DataFrame:
    return wide(df, country).corr()
