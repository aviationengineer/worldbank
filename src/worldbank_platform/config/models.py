"""Pydantic configuration models. No secrets live here."""
from __future__ import annotations

from pydantic import BaseModel, Field


class WorldBankSettings(BaseModel):
    base_url: str = "https://api.worldbank.org/v2"
    timeout_seconds: int = 30
    per_page: int = 1000


class DateRange(BaseModel):
    start: int = 2000
    end: int = 2025


class HttpSettings(BaseModel):
    max_attempts: int = 4
    backoff_base_seconds: float = 2.0
    backoff_multiplier: float = 2.0
    max_backoff_seconds: float = 60.0
    respect_retry_after: bool = True
    max_workers: int = 4
    ca_bundle: str | None = None


class StorageSettings(BaseModel):
    base_dir: str = "data"
    raw_dir: str = "data/raw"
    processed_dir: str = "data/processed"
    analytics_dir: str = "data/analytics"
    cache_ttl_seconds: int = 86400


class QualityWeights(BaseModel):
    completeness: float = 0.30
    uniqueness: float = 0.20
    validity: float = 0.20
    consistency: float = 0.20
    freshness: float = 0.10


class QualitySettings(BaseModel):
    weights: QualityWeights = Field(default_factory=QualityWeights)
    min_quality_score: float = 0.70
    flag_negative_gdp: bool = True
    flag_negative_population: bool = True
    inflation_abs_limit: float = 1000.0


class SheetsSettings(BaseModel):
    spreadsheet_id: str = ""
    auth_mode: str = "connector"  # 'service_account' | 'connector'


class LoggingSettings(BaseModel):
    level: str = "INFO"
    structured: bool = True
    dir: str = "logs"


class SourceDefinition(BaseModel):
    connector: str
    enabled: bool = True
    priority: str = "P2"
    refresh: str = "weekly"
    description: str = ""


class AppConfig(BaseModel):
    worldbank: WorldBankSettings = Field(default_factory=WorldBankSettings)
    date_range: DateRange = Field(default_factory=DateRange)
    countries: list[str] = Field(default_factory=list)
    http: HttpSettings = Field(default_factory=HttpSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    quality: QualitySettings = Field(default_factory=QualitySettings)
    sheets: SheetsSettings = Field(default_factory=SheetsSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    sources: dict[str, SourceDefinition] = Field(default_factory=dict)
    indicators: dict[str, dict] = Field(default_factory=dict)
