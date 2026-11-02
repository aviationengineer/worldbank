# Operations

## Run modes

```bash
worldbank ingest --mode full          # everything configured
worldbank ingest --mode incremental   # only new since last state
worldbank ingest --mode backfill      # re-pull a window (uses date_range)
```

State lives in `metadata/ingestion_state.json` (per source+endpoint:
last run, last record date, record count).

## Observability

- Structured JSON logs in `logs/`
- `logs/audit.jsonl`: one record per run (`run_id` like `WB-2026-11-01-001`)
- `worldbank status`: per-source freshness at a glance
- Example run summary printed by the CLI after each ingest

## Scheduling

- Cron: `0 6 * * * worldbank ingest --all && worldbank publish --google-sheets`
- GitHub Actions / Cloud Scheduler / Airflow: call the same CLI.
