"""Integration tests against the live World Bank API (needs network)."""
import pytest

from worldbank_platform.config.loader import load_config
from worldbank_platform.connectors.worldbank import WorldBankClient

pytestmark = pytest.mark.integration


def test_live_indicator_request():
    cfg = load_config()
    client = WorldBankClient(cfg)
    try:
        items = list(client.paged(
            "country/CA/indicator/NY.GDP.MKTP.CD",
            {"date": "2023:2024", "per_page": 10}).items())
    finally:
        client.close()
    assert len(items) == 2
    assert items[0]["country"]["id"] == "CA"
