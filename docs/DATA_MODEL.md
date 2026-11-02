# Data Model

## dim_country (`02_Country`)

One row per country/economy: `country_code` (ISO3), `country_name`, `iso2`,
`iso3`, `region`, `income_level`, `lending_type`, `capital`, `latitude`, `longitude`.

## dim_indicator (catalog in `03_Indicator_Catalog`)

`indicator_code`, `indicator_name`, `description`, `unit`, `source`,
`source_organization`, `topic`.

## fact_indicators (`04_Indicators`, long format)

`country_code`, `country_name`, `indicator_code`, `indicator_name`, `year`,
`value`, `unit`, `source`, `ingestion_timestamp`. Natural key:
`(country_code, indicator_code, year)`.

## Ops tables

- `07_Data_Quality`: `run_id`, `dataset`, `record_count`, `null_count`, `duplicate_count`, `quality_score`, `validation_status`, `run_timestamp`
- `08_Ingestion_Log`: `run_id`, `source`, `endpoint`, `start_time`, `end_time`, `records_extracted`, `records_loaded`, `status`, `error_message`
- `09_Data_Lineage`: `dataset`, `source_api`, `endpoint`, `extraction_timestamp`, `transformation`, `destination`

## AI-ready document shape

```json
{"dataset": "world_development_indicators", "country": "Canada",
 "indicator": "GDP", "year": 2024, "value": 2251986878174.0,
 "source": "World Bank", "source_url": "https://api.worldbank.org/v2/...",
 "retrieved_at": "..."}
```
