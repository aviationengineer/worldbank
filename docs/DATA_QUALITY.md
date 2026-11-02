# Data Quality

Five dimensions, weighted into `quality_score`:

```
quality_score = completeness*0.30 + uniqueness*0.20 + validity*0.20
              + consistency*0.20 + freshness*0.10
```

| Dimension | What it measures |
|---|---|
| Completeness | 1 − null fraction over required columns |
| Uniqueness | 1 − duplicate fraction on the natural key |
| Validity | Country codes are ISO3-like; years in 1960–2030 |
| Consistency | Domain rules (e.g. population ≥ 0); anomalies **flagged, never rejected** |
| Freshness | 1.0 for freshly ingested data |

Runs scoring below `quality.min_quality_score` (default 0.70) are marked
`REVIEW`; the pipeline still lands the data and records anomalies in the
audit log. Legitimate-but-unusual World Bank values are never dropped.
