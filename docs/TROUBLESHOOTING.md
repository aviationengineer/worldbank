# Troubleshooting

## `WorldBankError: Unexpected envelope`

The API returned an error object (bad country/indicator code). Check the code
against `worldbank list-indicators` / the API docs.

## 429 / rate limiting

Retries with backoff are automatic. If persistent, lower `http.max_workers`
or raise `backoff_base_seconds` in `config/settings.yaml`.

## Empty datasets

Some indicator × country × year combos have no data — the connector yields
zero records and the pipeline continues. Check `08_Ingestion_Log`.

## Google Sheets: "No spreadsheet id"

Set `GOOGLE_SHEET_ID` in `.env` or pass `--spreadsheet` to `publish`.

## Google Sheets: permission denied (service account)

Share the spreadsheet with the service-account email as Editor.

## Quality status REVIEW

See `quality.anomalies` in the run output / audit log. Data still lands;
only the flag changes.
