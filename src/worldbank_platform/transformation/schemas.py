"""Pydantic record schemas for curated datasets."""
from __future__ import annotations

from pydantic import BaseModel, Field


class IndicatorRecord(BaseModel):
    country_code: str | None = None
    country_name: str | None = None
    indicator_code: str | None = None
    indicator_name: str | None = None
    year: int | None = None
    value: float | None = None
    unit: str | None = None
    source: str = "World Bank"
    topic: str | None = None
    ingestion_timestamp: str | None = None


class CountryRecord(BaseModel):
    country_code: str | None = None
    country_name: str | None = None
    iso2: str | None = None
    iso3: str | None = None
    region: str | None = None
    income_level: str | None = None
    lending_type: str | None = None
    capital: str | None = None
    latitude: float | None = None
    longitude: float | None = None
