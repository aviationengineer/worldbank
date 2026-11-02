"""Unit tests: config loading."""
from worldbank_platform.config.loader import load_config


def test_config_loads():
    cfg = load_config()
    assert cfg.worldbank.base_url.startswith("https://")
    assert "CA" in cfg.countries
    assert "NY.GDP.MKTP.CD" in cfg.indicators
    assert cfg.sources["worldbank_indicators"].enabled is True
    assert cfg.sources["worldbank_projects"].enabled is False
    assert abs(sum(cfg.quality.weights.model_dump().values()) - 1.0) < 1e-9
