"""Validate the environment: Python version, config, packages, API, sheet."""
from __future__ import annotations

import importlib
import os
import sys

REQUIRED = ["httpx", "tenacity", "pydantic", "pandas", "pyarrow",
            "yaml", "dotenv", "click", "plotly", "sklearn"]


def check(label: str, ok: bool, detail: str = "") -> bool:
    print(f"[{'OK' if ok else 'FAIL'}] {label} {detail}")
    return ok


def main() -> int:
    ok = True
    ok &= check("Python >= 3.11", sys.version_info >= (3, 11), sys.version.split()[0])
    for pkg in REQUIRED:
        try:
            importlib.import_module(pkg)
            ok &= check(f"package {pkg}", True)
        except ImportError:
            ok &= check(f"package {pkg}", False, "(pip install -r requirements.txt)")
    sys.path.insert(0, "src")
    try:
        from worldbank_platform.config.loader import load_config
        cfg = load_config()
        ok &= check("config loads", True, f"{len(cfg.countries)} countries, "
                                          f"{len(cfg.indicators)} indicators")
    except Exception as exc:
        ok &= check("config loads", False, str(exc))
        return 1
    try:
        from worldbank_platform.connectors.worldbank import WorldBankClient
        client = WorldBankClient(cfg)
        items = list(client.paged("country/CA/indicator/NY.GDP.MKTP.CD",
                                  {"date": "2024", "per_page": 5}).items())
        client.close()
        ok &= check("World Bank API reachable", len(items) > 0, f"{len(items)} rows")
    except Exception as exc:
        ok &= check("World Bank API reachable", False, str(exc)[:120])
    sheet = os.environ.get("GOOGLE_SHEET_ID", cfg.sheets.spreadsheet_id)
    ok &= check("Google Sheet configured", bool(sheet), sheet or "(set GOOGLE_SHEET_ID)")
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print("[INFO] GOOGLE_APPLICATION_CREDENTIALS unset: connector transport will be used")
    print("\nBootstrap " + ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
