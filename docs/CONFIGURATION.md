# Configuration

All behavior is driven by `config/*.yaml` — no code changes needed for
routine changes.

| File | Purpose |
|---|---|
| `settings.yaml` | Base URL, date range, HTTP retry policy, storage paths, quality weights, Sheets mode |
| `countries.yaml` | ISO3 country list |
| `indicators.yaml` | Indicator code → name/unit/topic |
| `sources.yaml` | Source registry: connector, enabled, priority, refresh cadence |
| `sheets.yaml` | Spreadsheet title + worksheet column layouts |

## Environment overrides

| Variable | Effect |
|---|---|
| `GOOGLE_SHEET_ID` | Target spreadsheet (overrides `sheets.spreadsheet_id`) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Service-account JSON path; also switches `auth_mode` to `service_account` |
| `WB_BASE_URL` | API base URL override |
| `WB_LOG_LEVEL` | Logging level |
| `GWS_CLI` | Connector-transport CLI path (local dev) |

## Adding an indicator

Add one line to `config/indicators.yaml`:

```yaml
NY.GNP.PCAP.CD: {name: "GNI per capita (current US$)", unit: "US$", topic: "Economy"}
```

## Adding a country

Add the ISO3 code to `config/countries.yaml`.
