# API Connectors

## Adding a new connector (any REST API: IMF, OECD, UN, WHO, …)

1. Create `src/worldbank_platform/connectors/mydatasource.py`:

```python
from typing import Any, Iterator
from .base import BaseConnector, ConnectorResult, register

@register("mydatasource")
class MyDataSourceConnector(BaseConnector):
    def fetch(self, **kwargs: Any) -> Iterator[ConnectorResult]:
        # use WorldBankClient-style HTTP or your own client;
        # yield ConnectorResult(source=..., endpoint=..., records=[...], raw_pages=[...])
        ...
```

2. Register it in `config/sources.yaml`:

```yaml
mydatasource:
  connector: mydatasource
  enabled: true
  priority: P1
  refresh: weekly
  description: "My new source"
```

3. Add a Pydantic schema in `transformation/schemas.py` and map it in
   `Normalizer.SCHEMAS`, plus dedupe keys in `Standardizer.DEDUPE_KEYS`.

No pipeline, CLI, or Sheets code changes are needed.

## World Bank specifics

- Base: `https://api.worldbank.org/v2`, public, no key.
- Envelope: `[meta, data]`; `meta` carries `page/pages/per_page/total`.
- `WorldBankClient.paged(path, params)` auto-iterates pages.
- Retries: tenacity exponential backoff (2s → 4s → 8s …), honors 429/5xx and `Retry-After`.
