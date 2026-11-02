# Deployment

## Docker / Kubernetes

```bash
docker build -t worldbank-platform .
docker run --env-file .env worldbank-platform ingest --all
```

Inject `GOOGLE_APPLICATION_CREDENTIALS` (mounted secret) and `GOOGLE_SHEET_ID`
at runtime — never bake them into the image.

## Google Cloud Run

```bash
gcloud run deploy worldbank-platform --source . \
  --set-env-vars GOOGLE_SHEET_ID=<id> \
  --set-secrets GOOGLE_APPLICATION_CREDENTIALS=wb-sa-key:latest
```

## Cloud Functions / Cloud Composer

Wrap `Pipeline().run_all()` in the function handler / Airflow `PythonOperator`.
The CLI is the stable interface: `worldbank ingest --all`.

## BigQuery / Vertex AI

Curated Parquet in `data/processed/` loads directly with
`pandas.read_parquet` or `bq load`. The AI-ready document shape
(`docs/DATA_MODEL.md`) feeds RAG pipelines (LangChain/LlamaIndex/vector DBs).

## GitHub Actions

```yaml
- run: pip install -r requirements.txt
- run: worldbank ingest --all && worldbank publish --google-sheets
  env:
    GOOGLE_SHEET_ID: ${{ secrets.GOOGLE_SHEET_ID }}
```
