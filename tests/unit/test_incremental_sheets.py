"""Unit tests: incremental state store, sheets writer (fake transport)."""
import pandas as pd

from worldbank_platform.google_sheets.client import SheetsTransport
from worldbank_platform.google_sheets.writer import GoogleSheetsWriter
from worldbank_platform.ingestion.incremental import IngestMode, StateStore


class FakeTransport(SheetsTransport):
    def __init__(self):
        self.sheets: dict[str, list] = {}
        self.created: list[str] = []

    def create_spreadsheet(self, title: str) -> str:
        self.created.append(title)
        return "fake-id"

    def ensure_worksheet(self, spreadsheet_id: str, title: str) -> None:
        self.sheets.setdefault(title, [])

    def clear(self, spreadsheet_id: str, sheet: str) -> None:
        self.sheets[sheet] = []

    def write_values(self, spreadsheet_id: str, sheet: str, values) -> None:
        self.sheets[sheet] = values

    def append_values(self, spreadsheet_id: str, sheet: str, values) -> None:
        self.sheets[sheet].extend(values)


def test_state_store_roundtrip(tmp_path):
    store = StateStore(tmp_path / "state.json")
    st = store.get("worldbank_indicators", "country/CA/indicator/X")
    st.touch(record_count=10, last_record_date="2024")
    store.save()
    store2 = StateStore(tmp_path / "state.json")
    st2 = store2.get("worldbank_indicators", "country/CA/indicator/X")
    assert st2.record_count == 10 and st2.last_record_date == "2024"
    assert IngestMode.FULL and IngestMode.INCREMENTAL and IngestMode.BACKFILL


def test_writer_replace_and_append():
    t = FakeTransport()
    w = GoogleSheetsWriter(t, "fake-id")
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    w.write_dataframe("S1", df)
    assert t.sheets["S1"][0] == ["a", "b"] and len(t.sheets["S1"]) == 3
    w.append_dataframe("S1", df)
    assert len(t.sheets["S1"]) == 5
    w.clear_worksheet("S1")
    assert t.sheets["S1"] == []
