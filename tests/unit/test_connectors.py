"""Unit tests: connector normalization."""
import json
from pathlib import Path
from unittest.mock import MagicMock

import httpx

from worldbank_platform.config.loader import load_config
from worldbank_platform.connectors import indicators as ind_mod
from worldbank_platform.connectors import countries as cty_mod
from worldbank_platform.connectors.base import get_connector, registered_connectors

FIX = Path(__file__).parents[1] / "fixtures"


def _http(pages):
    http = MagicMock(spec=httpx.Client)

    def get(url, params=None):
        page = int(params.get("page", 1))
        r = MagicMock(spec=httpx.Response)
        r.status_code = 200
        r.headers = {}
        r.json.return_value = pages[page]
        r.raise_for_status.return_value = None
        return r

    http.get.side_effect = get
    return http


def test_registry_lists_phase1_and_phase2():
    names = registered_connectors()
    assert "indicators" in names and "countries" in names
    assert "projects" in names  # Phase-2 stub registered


def test_indicators_normalize():
    cfg = load_config()
    conn = get_connector("indicators", cfg)
    pages = {1: json.loads((FIX / "wb_indicators_page1.json").read_text()),
             2: json.loads((FIX / "wb_indicators_page2.json").read_text())}
    conn.client = ind_mod.WorldBankClient(cfg, http=_http(pages))
    results = list(conn.fetch(country="CA", indicator="NY.GDP.MKTP.CD"))
    recs = results[0].records
    assert len(recs) == 4
    r0 = recs[0]
    assert r0["country_code"] == "CA" and r0["year"] == 2024
    assert r0["value"] == 2251986878174.0
    assert recs[3]["value"] is None  # null preserved, not dropped


def test_countries_normalize():
    cfg = load_config()
    conn = get_connector("countries", cfg)
    pages = {1: json.loads((FIX / "wb_countries.json").read_text())}
    conn.client = cty_mod.WorldBankClient(cfg, http=_http(pages))
    recs = list(conn.fetch())[0].records
    assert len(recs) == 2
    ca = recs[0]
    assert ca["country_code"] == "CAN" and ca["iso2"] == "CA"
    assert ca["capital"] == "Ottawa"
    assert ca["latitude"] == 45.42


def test_phase2_stub_raises():
    cfg = load_config()
    conn = get_connector("projects", cfg)
    with __import__("pytest").raises(NotImplementedError):
        list(conn.fetch())
