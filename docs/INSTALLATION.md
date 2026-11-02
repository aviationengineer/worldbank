# Installation

## Requirements

- Python 3.11+
- pip

## Steps

```bash
git clone <repository>
cd worldbank-data-platform
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .                   # installs the `worldbank` CLI
cp .env.example .env
python scripts/bootstrap.py
```

`bootstrap.py` validates the Python version, required packages, configuration,
World Bank API connectivity, and whether a Google Sheet is configured.

## Docker

```bash
docker build -t worldbank-platform .
docker run --env-file .env worldbank-platform ingest --all
# or
docker compose up
```
