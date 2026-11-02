"""Source registry + data-product registry -> sheet-ready rows."""
from __future__ import annotations

from ..config.models import AppConfig
from ..utils.dates import utcnow_iso

DATA_PRODUCTS = [
    {"product_id": "WB-DP-001", "product_name": "World Development Indicators",
     "description": "Economic and development indicators (country x indicator x year)",
     "source": "World Bank", "owner": "Economic Intelligence",
     "business_domain": "Macroeconomics", "classification": "Public",
     "criticality": "P1", "refresh_frequency": "Weekly", "sla": "99%",
     "quality_threshold": 0.70, "schema_version": "v1.0", "status": "Active",
     "consumers": "Google Sheets, Parquet, analytics"},
    {"product_id": "WB-DP-002", "product_name": "Country Reference (dim_country)",
     "description": "Standardized country dimension",
     "source": "World Bank", "owner": "Economic Intelligence",
     "business_domain": "Reference data", "classification": "Public",
     "criticality": "P1", "refresh_frequency": "Monthly", "sla": "99%",
     "quality_threshold": 0.90, "schema_version": "v1.0", "status": "Active",
     "consumers": "Google Sheets, Parquet, analytics"},
]


class Catalog:
    def __init__(self, config: AppConfig):
        self.config = config

    def source_rows(self, last_run: str | None = None) -> list[dict]:
        stamp = last_run or utcnow_iso()
        rows = []
        for sid, spec in self.config.sources.items():
            rows.append({
                "source_id": sid,
                "source_name": spec.description or sid,
                "api_type": "REST",
                "base_url": self.config.worldbank.base_url,
                "documentation_url": "https://datahelpdesk.worldbank.org/knowledgebase/articles/889392",
                "owner": "World Bank",
                "description": spec.description,
                "refresh_frequency": spec.refresh,
                "status": "enabled" if spec.enabled else "disabled",
                "last_run": stamp,
            })
        return rows

    def dataset_rows(self) -> list[dict]:
        return [
            {"dataset_id": p["product_id"], "dataset_name": p["product_name"],
             "description": p["description"], "publisher": p["source"],
             "last_updated": utcnow_iso(), "topic": p["business_domain"],
             "resource_url": "https://data.worldbank.org"}
            for p in DATA_PRODUCTS
        ]
