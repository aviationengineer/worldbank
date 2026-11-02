# World Bank Data Platform

Enterprise Python data ingestion & intelligence framework for World Bank APIs —
discover, extract, validate, transform, catalog, and publish public economic and
development data to Google Sheets, Parquet, and analytics.

## What it does

- **Discovers & extracts** World Bank v2 REST APIs (indicators, countries; projects/finance/poverty/climate/documents/catalog/SDMX are Phase-2-ready stubs)
- **Handles** pagination, retries with exponential backoff, rate limits, incremental loads
- **Validates** with a 5-dimension data-quality score (completeness, uniqueness, validity, consistency, freshness)
- **Stores** raw JSON + curated Parquet, tracks lineage and audit logs per run
- **Publishes** to a 10-worksheet "World Bank Data Intelligence" Google Sheet
- **Analyzes**: growth rates, CAGR, rankings, correlations, outlier detection, natural-language summaries
- **Visualizes**: Plotly charts + HTML dashboard

## Quickstart

```bash
git clone <repository>
cd worldbank-data-platform
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env   # add GOOGLE_SHEET_ID when ready

python scripts/bootstrap.py
worldbank ingest --country CA --indicator NY.GDP.MKTP.CD
worldbank publish --google-sheets
worldbank status
```

## CLI

```
worldbank list-sources | list-indicators | list-countries
worldbank ingest --source indicators | --all | --country CA | --indicator NY.GDP.MKTP.CD
worldbank ingest --mode incremental
worldbank publish --google-sheets
worldbank profile | quality | status
```

## Docs

- `docs/ARCHITECTURE.md` — components + Mermaid diagrams
- `docs/INSTALLATION.md`, `docs/CONFIGURATION.md`, `docs/GOOGLE_SHEETS.md`
- `docs/API_CONNECTORS.md` — how to add a new API
- `docs/DATA_MODEL.md`, `docs/DATA_QUALITY.md`, `docs/OPERATIONS.md`
- `docs/DEVELOPMENT.md`, `docs/DEPLOYMENT.md`, `docs/TROUBLESHOOTING.md`

## Project layout

See `docs/ARCHITECTURE.md`. Config lives in `config/*.yaml` — add countries,
indicators, or sources without touching Python.
