"""Sheets auth abstraction.

Two transports:
- ServiceAccountTransport: gspread + GOOGLE_APPLICATION_CREDENTIALS (enterprise).
- ConnectorTransport: the runtime's hatch_gws_cli (local dev / this environment).

The writer talks to the transport interface, so deployments pick one
without changing pipeline code.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from typing import Any

log = logging.getLogger("worldbank.sheets")


class SheetsTransport(ABC):
    @abstractmethod
    def create_spreadsheet(self, title: str) -> str:
        """Create a spreadsheet; return its id."""

    @abstractmethod
    def ensure_worksheet(self, spreadsheet_id: str, title: str) -> None:
        """Create the worksheet if missing."""

    @abstractmethod
    def clear(self, spreadsheet_id: str, sheet: str) -> None: ...

    @abstractmethod
    def write_values(self, spreadsheet_id: str, sheet: str,
                     values: list[list[Any]]) -> None: ...

    @abstractmethod
    def append_values(self, spreadsheet_id: str, sheet: str,
                      values: list[list[Any]]) -> None: ...


class ServiceAccountTransport(SheetsTransport):
    """Enterprise path: gspread with a service-account JSON key."""

    def __init__(self, credentials_path: str | None = None):
        import gspread  # lazy: only needed on this path
        self._gspread = gspread
        path = credentials_path or os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
        self._client = gspread.service_account(filename=path)

    def _sh(self, spreadsheet_id: str):
        return self._client.open_by_key(spreadsheet_id)

    def create_spreadsheet(self, title: str) -> str:
        return self._sh(self._client.create(title).id).id

    def ensure_worksheet(self, spreadsheet_id: str, title: str) -> None:
        sh = self._sh(spreadsheet_id)
        if title not in [ws.title for ws in sh.worksheets()]:
            sh.add_worksheet(title=title, rows=1000, cols=26)

    def clear(self, spreadsheet_id: str, sheet: str) -> None:
        self._sh(spreadsheet_id).worksheet(sheet).clear()

    def write_values(self, spreadsheet_id: str, sheet: str,
                     values: list[list[Any]]) -> None:
        ws = self._sh(spreadsheet_id).worksheet(sheet)
        ws.update(values, value_input_option="USER_ENTERED")

    def append_values(self, spreadsheet_id: str, sheet: str,
                      values: list[list[Any]]) -> None:
        ws = self._sh(spreadsheet_id).worksheet(sheet)
        ws.append_rows(values, value_input_option="USER_ENTERED")


class ConnectorTransport(SheetsTransport):
    """Local-dev path: shell out to the runtime's Sheets connector CLI."""

    def __init__(self, cli: str | None = None):
        self.cli = cli or os.environ.get("GWS_CLI", "/opt/hatch/bin/hatch_gws_cli")

    def _run(self, *args: str, body: dict | None = None) -> Any:
        cmd = [self.cli, "sheets", *args]
        if body is not None:
            cmd += ["--json", json.dumps(body)]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if proc.returncode != 0:
            raise RuntimeError(f"sheets CLI failed: {(proc.stdout + proc.stderr)[-600:]}")
        out = proc.stdout.strip()
        start = out.find("{")
        if start < 0:
            start = out.find("[")
        return json.loads(out[start:]) if start >= 0 else {}

    def create_spreadsheet(self, title: str) -> str:
        data = self._run("spreadsheets", "create",
                         body={"properties": {"title": title}})
        return data["spreadsheetId"]

    def _sheet_id(self, spreadsheet_id: str, title: str) -> int | None:
        meta = self._run("spreadsheets", "get",
                         "--params", json.dumps({"spreadsheetId": spreadsheet_id}))
        for sh in meta.get("sheets", []):
            props = sh.get("properties", {})
            if props.get("title") == title:
                return props.get("sheetId")
        return None

    def ensure_worksheet(self, spreadsheet_id: str, title: str) -> None:
        if self._sheet_id(spreadsheet_id, title) is None:
            self._run("spreadsheets", "batchUpdate",
                      "--params", json.dumps({"spreadsheetId": spreadsheet_id}),
                      body={"requests": [{"addSheet": {"properties": {"title": title}}}]})

    def clear(self, spreadsheet_id: str, sheet: str) -> None:
        self._run("spreadsheets", "values", "clear",
                  "--params", json.dumps({"spreadsheetId": spreadsheet_id,
                                          "range": f"{sheet}!A:ZZ"}))

    def _col(self, n: int) -> str:
        name = ""
        while n > 0:
            n, r = divmod(n - 1, 26)
            name = chr(65 + r) + name
        return name

    def write_values(self, spreadsheet_id: str, sheet: str,
                     values: list[list[Any]]) -> None:
        if not values:
            return
        end = self._col(max(len(r) for r in values))
        rng = f"{sheet}!A1:{end}{len(values)}"
        self._run("spreadsheets", "values", "update",
                  "--params", json.dumps({"spreadsheetId": spreadsheet_id,
                                          "range": rng,
                                          "valueInputOption": "USER_ENTERED"}),
                  body={"values": values})

    def append_values(self, spreadsheet_id: str, sheet: str,
                      values: list[list[Any]]) -> None:
        if not values:
            return
        self._run("spreadsheets", "values", "append",
                  "--params", json.dumps({"spreadsheetId": spreadsheet_id,
                                          "range": f"{sheet}!A:A",
                                          "valueInputOption": "USER_ENTERED"}),
                  body={"values": values})

    def batch_format(self, spreadsheet_id: str, requests: list[dict]) -> None:
        if requests:
            self._run("spreadsheets", "batchUpdate",
                      "--params", json.dumps({"spreadsheetId": spreadsheet_id}),
                      body={"requests": requests})


def make_transport(auth_mode: str) -> SheetsTransport:
    if auth_mode == "service_account":
        return ServiceAccountTransport()
    return ConnectorTransport()
