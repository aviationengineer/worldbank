"""Number/date formatting helpers for sheet values."""
from __future__ import annotations

import pandas as pd


def format_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Light, transport-safe formatting: ISO dates, rounded floats."""
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].dt.strftime("%Y-%m-%d")
        elif pd.api.types.is_float_dtype(out[col]):
            out[col] = out[col].round(4)
    return out
