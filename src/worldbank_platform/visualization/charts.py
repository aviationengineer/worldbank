"""Plotly charts for indicator data."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def gdp_trend(df: pd.DataFrame, country: str, indicator: str = "NY.GDP.MKTP.CD"):
    s = df[(df["country_code"] == country) & (df["indicator_code"] == indicator)]
    s = s.dropna(subset=["value"]).sort_values("year")
    fig = px.line(s, x="year", y="value",
                  title=f"{indicator} — {country} (World Bank)")
    fig.update_layout(xaxis_title="Year", yaxis_title="Value")
    return fig


def country_comparison(df: pd.DataFrame, indicator: str, year: int):
    s = df[(df["indicator_code"] == indicator) & (df["year"] == year)]
    s = s.dropna(subset=["value"]).sort_values("value", ascending=False)
    fig = px.bar(s, x="country_name", y="value",
                 title=f"{indicator} by country, {year} (World Bank)")
    return fig


def indicator_heatmap(df: pd.DataFrame, indicator: str):
    piv = df[df["indicator_code"] == indicator].pivot_table(
        index="country_name", columns="year", values="value", aggfunc="last")
    fig = go.Figure(data=go.Heatmap(z=piv.values, x=piv.columns, y=piv.index,
                                    colorscale="Viridis"))
    fig.update_layout(title=f"{indicator}: country x year")
    return fig
