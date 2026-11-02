"""Thin wrapper: python scripts/publish.py"""
import sys

sys.path.insert(0, "src")
from worldbank_platform.cli.main import cli

if __name__ == "__main__":
    sys.argv = ["worldbank", "publish", "--google-sheets", *sys.argv[1:]]
    cli()
