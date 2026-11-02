# Development

## Tests

```bash
pytest tests/unit -q            # fast, mocked — no network
pytest tests/integration -q     # live World Bank API
pytest -q                       # everything
```

Fixtures in `tests/fixtures/` cover: success, empty, malformed, pagination,
API failure, and rate limiting. Target: 80%+ meaningful coverage.

## Conventions

- Type hints everywhere; Pydantic for config and record schemas.
- New API = new connector (`connectors/base.py` contract), never pipeline edits.
- Structured logging; never log credentials.
- Keep Phase-2 stubs honest: `NotImplementedError` with the enablement path.
