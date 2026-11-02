"""HTML dashboard builder (Plotly figures -> single HTML file)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .charts import country_comparison, gdp_trend


def build_dashboard(df: pd.DataFrame, output: str | Path,
                    countries: list[str] | None = None) -> Path:
    """Write a small multi-chart HTML dashboard."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    countries = countries or sorted(df["country_code"].dropna().unique().tolist())
    parts = ["<html><head><meta charset='utf-8'><title>World Bank Dashboard</title></head><body>",
             "<h1>World Bank Data Intelligence — dashboard</h1>"]
    for cc in countries[:8]:
        fig = gdp_trend(df, cc)
        parts.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))
    latest_year = int(df["year"].max())
    fig = country_comparison(df, "NY.GDP.MKTP.CD", latest_year)
    parts.append(fig.to_html(full_html=False, include_plotlyjs=False))
    parts.append("</body></html>")
    output.write_text("\n".join(parts), encoding="utf-8")
    return output
