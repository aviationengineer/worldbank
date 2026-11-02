"""Thin wrapper: python scripts/ingest.py --all"""
import sys

sys.path.insert(0, "src")
from worldbank_platform.cli.main import cli

if __name__ == "__main__":
    sys.argv = ["worldbank", "ingest", *sys.argv[1:]]
    cli()
