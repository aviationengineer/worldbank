"""Declarative expectations per dataset."""
from __future__ import annotations

EXPECTATIONS: dict[str, dict] = {
    "worldbank_indicators": {
        "required_columns": ["country_code", "indicator_code", "year", "value"],
        "non_negative": ["value"],  # checked per-indicator below
        "unique_key": ["country_code", "indicator_code", "year"],
    },
    "worldbank_countries": {
        "required_columns": ["country_code", "country_name", "iso2", "iso3"],
        "unique_key": ["country_code"],
    },
}

# Indicators where negative values are legitimate (growth rates, etc.)
ALLOW_NEGATIVE = {"NY.GDP.MKTP.KD.ZG", "FP.CPI.TOTL.ZG", "SL.UEM.TOTL.ZS"}
