"""Unit tests: normalizer, standardizer, validator, profiler."""
import pandas as pd

from worldbank_platform.config.loader import load_config
from worldbank_platform.quality.profiler import profile
from worldbank_platform.quality.validator import Validator
from worldbank_platform.transformation.normalizer import Normalizer
from worldbank_platform.transformation.standardizer import Standardizer


def _indicator_rows():
    return [
        {"country_code": "ca", "country_name": "Canada", "indicator_code": "NY.GDP.MKTP.CD",
         "indicator_name": "GDP", "year": "2024", "value": "2251986878174.0",
         "unit": "US$", "source": "World Bank", "topic": "Economy"},
        {"country_code": "CA", "country_name": "Canada", "indicator_code": "NY.GDP.MKTP.CD",
         "indicator_name": "GDP", "year": 2024, "value": 2251986878174.0,
         "unit": "US$", "source": "World Bank", "topic": "Economy"},  # duplicate
        {"country_code": "CA", "country_name": "Canada", "indicator_code": "SP.POP.TOTL",
         "indicator_name": "Population", "year": 2024, "value": -5,
         "unit": "persons", "source": "World Bank", "topic": "Population"},  # anomaly
    ]


def test_normalize_standardize_dedupe():
    df = Normalizer().normalize("worldbank_indicators", _indicator_rows())
    df = Standardizer().standardize("worldbank_indicators", df)
    assert len(df) == 2  # duplicate collapsed
    assert set(df["country_code"]) == {"CA"}
    assert str(df["year"].dtype).startswith("Int")


def test_quality_score_and_anomaly_flag():
    cfg = load_config()
    df = Standardizer().standardize(
        "worldbank_indicators",
        Normalizer().normalize("worldbank_indicators", _indicator_rows()))
    report = Validator(cfg.quality).validate("worldbank_indicators", df)
    assert report.duplicate_count == 0  # deduped upstream
    assert any("Negative population" in a for a in report.anomalies)
    assert 0.0 <= report.quality_score <= 1.0
    assert report.validation_status in ("PASS", "REVIEW")


def test_profiler():
    df = pd.DataFrame({"a": [1, 2, None], "b": ["x", "y", "z"]})
    p = profile(df)
    assert p["record_count"] == 3 and p["column_count"] == 2
    assert p["columns"]["a"]["null_pct"] > 0
