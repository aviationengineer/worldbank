"""Unit tests: WorldBankClient pagination, errors, retry."""
import json
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from worldbank_platform.config.loader import load_config
from worldbank_platform.connectors.worldbank import WorldBankClient, WorldBankError

FIX = Path(__file__).parents[1] / "fixtures"


def _resp(payload, status=200):
    r = MagicMock(spec=httpx.Response)
    r.status_code = status
    r.headers = {}
    r.json.return_value = payload
    r.raise_for_status.return_value = None
    return r


def _client_with(pages: dict[int, object]):
    http = MagicMock(spec=httpx.Client)

    def get(url, params=None):
        page = int(params.get("page", 1))
        return _resp(pages[page])

    http.get.side_effect = get
    cfg = load_config()
    return WorldBankClient(cfg, http=http)


def _load(name):
    return json.loads((FIX / name).read_text())


def test_pagination_collects_all_pages():
    client = _client_with({1: _load("wb_indicators_page1.json"),
                           2: _load("wb_indicators_page2.json")})
    items = list(client.paged("country/CA/indicator/NY.GDP.MKTP.CD").items())
    assert len(items) == 4
    assert items[0]["date"] == "2024"


def test_empty_response():
    client = _client_with({1: _load("wb_indicators_empty.json")})
    assert list(client.paged("country/XX/indicator/NOPE").items()) == []


def test_malformed_envelope_raises():
    client = _client_with({1: _load("wb_indicators_malformed.json")})
    with pytest.raises(WorldBankError):
        list(client.paged("country/CA/indicator/BAD").items())


def test_retry_on_500_then_success():
    http = MagicMock(spec=httpx.Client)
    fail = _resp({}, 500)
    fail.raise_for_status.side_effect = httpx.HTTPStatusError(
        "err", request=MagicMock(), response=MagicMock(status_code=500, headers={}))
    ok = _resp(_load("wb_indicators_empty.json"))
    http.get.side_effect = [fail, ok]
    cfg = load_config()
    cfg.http.max_attempts = 2
    client = WorldBankClient(cfg, http=http)
    assert list(client.paged("country/CA/indicator/X").items()) == []
    assert http.get.call_count == 2
