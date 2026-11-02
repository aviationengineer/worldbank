# Google Sheets

## Spreadsheet: "World Bank Data Intelligence"

10 worksheets (columns in `config/sheets.yaml`):

1. `01_Source_Catalog` — source registry
2. `02_Country` — dim_country
3. `03_Indicator_Catalog` — indicator metadata
4. `04_Indicators` — long-format facts (country × indicator × year)
5. `05_Projects` — Phase 2
6. `06_Datasets` — data-product registry
7. `07_Data_Quality` — per-run quality scores
8. `08_Ingestion_Log` — per-run audit
9. `09_Data_Lineage` — dataset lineage
10. `10_Analytics` — latest-value summary

## Authentication: service account (enterprise)

1. Create a Google Cloud project.
2. Enable the Google Sheets API (and Drive API if needed).
3. Create a service account; download the JSON key.
4. Share the spreadsheet with the service-account email (Editor).
5. Set in `.env`:

```
GOOGLE_APPLICATION_CREDENTIALS=/secure/path/service-account.json
GOOGLE_SHEET_ID=<spreadsheet id>
```

The writer then uses `ServiceAccountTransport` (gspread). Never commit the JSON key.

## Local dev

Without `GOOGLE_APPLICATION_CREDENTIALS`, the `ConnectorTransport` uses the
runtime's Sheets connector — no service account needed.

## Writer behavior

`GoogleSheetsWriter` replaces worksheets per publish (clear + write), formats
headers (bold + freeze + filter), and never touches other spreadsheets.
Incremental appends are available via `append_dataframe()`.
