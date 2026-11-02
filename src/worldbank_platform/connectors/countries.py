"""Country API connector -> dim_country records."""
from __future__ import annotations

from typing import Any, Iterator

from ..config.models import AppConfig
from ..utils.helpers import safe_float
from .base import BaseConnector, ConnectorResult, register
from .worldbank import WorldBankClient


@register("countries")
class CountriesConnector(BaseConnector):
    """GET /country — one record per country/economy."""

    def __init__(self, config: AppConfig):
        super().__init__(config)
        self.client = WorldBankClient(config)

    def fetch(self, **kwargs: Any) -> Iterator[ConnectorResult]:
        records: list[dict] = []
        raw_pages: list[Any] = []
        for page in self.client.paged("country").pages():
            raw_pages.append({"page": page.page, "items": page.items})
            for row in page.items:
                records.append(self._normalize(row))
        yield ConnectorResult(source="worldbank_countries", endpoint="country",
                              records=records, raw_pages=raw_pages)

    def _normalize(self, row: dict) -> dict:
        region = row.get("region") or {}
        income = row.get("incomeLevel") or {}
        lending = row.get("lendingType") or {}
        return {
            "country_code": row.get("id"),
            "country_name": row.get("name"),
            "iso2": row.get("iso2Code"),
            "iso3": row.get("id"),
            "region": region.get("value"),
            "income_level": income.get("value"),
            "lending_type": lending.get("value"),
            "capital": row.get("capitalCity"),
            "latitude": safe_float(row.get("latitude")),
            "longitude": safe_float(row.get("longitude")),
        }
