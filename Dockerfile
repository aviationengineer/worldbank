FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY pyproject.toml .

RUN pip install --no-cache-dir -e .

# Credentials and sheet id are injected at runtime, never baked in.
# GOOGLE_APPLICATION_CREDENTIALS=/secrets/service-account.json
# GOOGLE_SHEET_ID=<spreadsheet id>

ENTRYPOINT ["worldbank"]
CMD ["status"]
