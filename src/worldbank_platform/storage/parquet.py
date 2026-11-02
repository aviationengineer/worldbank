"""Parquet read/write (PyArrow engine) with optional partitioning."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_parquet(df: pd.DataFrame, path: str | Path,
                  partition_cols: list[str] | None = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if partition_cols:
        df.to_parquet(path, engine="pyarrow", partition_cols=partition_cols)
    else:
        df.to_parquet(path, engine="pyarrow", index=False)
    return path


def read_parquet(path: str | Path) -> pd.DataFrame:
    return pd.read_parquet(path, engine="pyarrow")
