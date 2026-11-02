"""GoogleSheetsWriter: DataFrame-level publishing with formatting helpers."""
from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from .client import SheetsTransport

log = logging.getLogger("worldbank.sheets.writer")


class GoogleSheetsWriter:
    def __init__(self, transport: SheetsTransport, spreadsheet_id: str):
        self.t = transport
        self.spreadsheet_id = spreadsheet_id

    # -- spec'd surface -------------------------------------------------
    def create_spreadsheet(self, title: str) -> str:
        sid = self.t.create_spreadsheet(title)
        self.spreadsheet_id = sid
        return sid

    def create_worksheet(self, title: str) -> None:
        self.t.ensure_worksheet(self.spreadsheet_id, title)

    def write_dataframe(self, sheet: str, df: pd.DataFrame,
                        include_header: bool = True) -> None:
        """Full replace of a worksheet (clear + write)."""
        self.t.ensure_worksheet(self.spreadsheet_id, sheet)
        self.clear_worksheet(sheet)
        values = self._frame_to_values(df, include_header)
        self.t.write_values(self.spreadsheet_id, sheet, values)

    def append_dataframe(self, sheet: str, df: pd.DataFrame) -> None:
        self.t.ensure_worksheet(self.spreadsheet_id, sheet)
        self.t.append_values(self.spreadsheet_id, sheet,
                             self._frame_to_values(df, include_header=False))

    def replace_worksheet(self, sheet: str, df: pd.DataFrame) -> None:
        self.write_dataframe(sheet, df)

    def clear_worksheet(self, sheet: str) -> None:
        self.t.ensure_worksheet(self.spreadsheet_id, sheet)
        self.t.clear(self.spreadsheet_id, sheet)

    def format_header(self, sheet: str, ncols: int) -> None:
        """Bold header row with a light fill + freeze + filter (connector path)."""
        if not hasattr(self.t, "batch_format"):
            return
        sid = self.t._sheet_id(self.spreadsheet_id, sheet)  # type: ignore[attr-defined]
        if sid is None:
            return
        self.t.batch_format(self.spreadsheet_id, [  # type: ignore[attr-defined]
            {"repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1,
                          "startColumnIndex": 0, "endColumnIndex": ncols},
                "cell": {"userEnteredFormat": {
                    "textFormat": {"bold": True},
                    "backgroundColor": {"red": 0.9, "green": 0.93, "blue": 0.96}}},
                "fields": "userEnteredFormat(textFormat,backgroundColor)"}},
            {"updateSheetProperties": {
                "properties": {"sheetId": sid,
                               "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount"}},
            {"setBasicFilter": {"filter": {
                "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1,
                          "startColumnIndex": 0, "endColumnIndex": ncols}}}},
        ])

    def freeze_header(self, sheet: str) -> None:
        self.format_header(sheet, 26)  # formatting bundle includes the freeze

    def auto_resize(self, sheet: str) -> None:  # pragma: no cover - cosmetic
        log.debug("auto_resize is a no-op on the connector transport")

    def apply_number_format(self, sheet: str, col: int, pattern: str) -> None:  # pragma: no cover
        log.debug("apply_number_format is a no-op on the connector transport")

    def create_filter(self, sheet: str, ncols: int) -> None:
        self.format_header(sheet, ncols)

    # -- helpers ----------------------------------------------------------
    @staticmethod
    def _frame_to_values(df: pd.DataFrame, include_header: bool) -> list[list[Any]]:
        frame = df.where(pd.notna(df), "")
        values: list[list[Any]] = []
        if include_header:
            values.append(list(frame.columns))
        values.extend(frame.astype(object).values.tolist())
        return values
