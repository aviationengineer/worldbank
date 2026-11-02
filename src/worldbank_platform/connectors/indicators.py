"""World Development Indicators connector -> long-format indicator records."""
from __future__ import annotations

from typing import Any, Iterator

from ..config.models import AppConfig
from ..utils.helpers import safe_float, safe_int
from .base import BaseConnector, ConnectorResult, register
from .worldbank import WorldBankClient


@register("indicators")
class IndicatorsConnector(BaseConnector):
    """GET /country/{cc}/indicator/{code}?date={start}:{end}"""

    def __init__(self, config: AppConfig):
        super().__init__(config)
        self.client = WorldBankClient(config)
        self.catalog = config.indicators  # code -> {name, unit, topic}

    def fetch(self, country: str | None = None, indicator: str | None = None,
              **kwargs: Any) -> Iterator[ConnectorResult]:
        countries = [country] if country else self.config.countries
        codes = [indicator] if indicator else list(self.catalog)
        dr = self.config.date_range
        date_param = f"{dr.start}:{dr.end}"
        for cc in countries:
            for code in codes:
                path = f"country/{cc}/indicator/{code}"
                meta = self.catalog.get(code, {})
                records: list[dict] = []
                raw_pages: list[Any] = []
                for page in self.client.paged(path, {"date": date_param}).pages():
                    raw_pages.append({"page": page.page, "items": page.items})
                    for row in page.items:
                        records.append(self._normalize(row, code, meta))
                yield ConnectorResult(
                    source="worldbank_indicators", endpoint=path,
                    records=records, raw_pages=raw_pages)

    def _normalize(self, row: dict, code: str, meta: dict) -> dict:
        country = row.get("country") or {}
        indicator = row.get("indicator") or {}
        return {
            "country_code": country.get("id"),
            "country_name": country.get("value"),
            "indicator_code": indicator.get("id") or code,
            "indicator_name": indicator.get("value") or meta.get("name"),
            "year": safe_int(row.get("date")),
            "value": safe_float(row.get("value")),
            "unit": meta.get("unit"),
            "source": "World Bank",
            "topic": meta.get("topic"),
        }

    def list_indicators(self) -> list[dict]:
        return [{"code": c, **m} for c, m in self.catalog.items()]
