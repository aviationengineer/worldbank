"""CLI: worldbank list-sources | ingest | publish | profile | quality | status."""
from __future__ import annotations

import json

import click
import pandas as pd

from ..config.loader import load_config
from ..connectors.base import get_connector, registered_connectors
from ..ingestion.incremental import IngestMode
from ..pipeline import Pipeline
from ..quality.profiler import profile
from ..quality.validator import Validator
from ..storage.parquet import read_parquet
from ..utils.logging import get_logger

log = get_logger("worldbank.cli")


@click.group()
def cli() -> None:
    """World Bank Data Platform."""


@cli.command("list-sources")
def list_sources() -> None:
    cfg = load_config()
    for name, spec in cfg.sources.items():
        click.echo(f"{name:24} connector={spec.connector:12} "
                   f"enabled={spec.enabled} refresh={spec.refresh}")


@cli.command("list-indicators")
def list_indicators() -> None:
    cfg = load_config()
    for code, meta in cfg.indicators.items():
        click.echo(f"{code:22} {meta.get('name')}")


@cli.command("list-countries")
def list_countries() -> None:
    cfg = load_config()
    click.echo(", ".join(cfg.countries))


@cli.command("ingest")
@click.option("--source", default=None, help="Source name from sources.yaml")
@click.option("--all", "all_sources", is_flag=True, help="Ingest all enabled sources")
@click.option("--country", default=None, help="ISO3 country filter (indicators)")
@click.option("--indicator", default=None, help="Indicator code filter")
@click.option("--mode", default=IngestMode.FULL,
              type=click.Choice([IngestMode.FULL, IngestMode.INCREMENTAL, IngestMode.BACKFILL]))
def ingest(source: str | None, all_sources: bool, country: str | None,
           indicator: str | None, mode: str) -> None:
    pipe = Pipeline()
    filters = {k: v for k, v in {"country": country, "indicator": indicator}.items() if v}
    if all_sources or (not source and not filters):
        results = pipe.run_all(mode=mode)
    elif source:
        results = [pipe.run_source(source, mode=mode, **filters)]
    else:
        results = [pipe.run_source("worldbank_indicators", mode=mode, **filters)]
    for res in results:
        q = res.get("quality")
        score = f"{q.quality_score:.1%}" if q else "n/a"
        click.echo(f"[{res['status']}] {res['source']}: "
                   f"{res['records']} records, quality={score} run={res['run_id']}")


@cli.command("publish")
@click.option("--google-sheets", is_flag=True, help="Publish curated data to Google Sheets")
@click.option("--spreadsheet", default=None, help="Spreadsheet id override")
def publish(google_sheets: bool, spreadsheet: str | None) -> None:
    if not google_sheets:
        click.echo("Nothing to do: pass --google-sheets")
        return
    pipe = Pipeline()
    result = pipe.publish_sheets(spreadsheet_id=spreadsheet)
    click.echo(f"Published to {result['spreadsheet_id']}:")
    for sheet, count in result["published"].items():
        click.echo(f"  {sheet}: {count} rows")


@cli.command("profile")
@click.option("--dataset", default="worldbank_indicators")
def profile_cmd(dataset: str) -> None:
    pipe = Pipeline()
    pq = pipe.latest_parquet(dataset)
    if not pq:
        click.echo(f"No data for {dataset}; run ingest first.")
        return
    click.echo(json.dumps(profile(read_parquet(pq)), indent=2, default=str))


@cli.command("quality")
@click.option("--dataset", default="worldbank_indicators")
def quality_cmd(dataset: str) -> None:
    pipe = Pipeline()
    pq = pipe.latest_parquet(dataset)
    if not pq:
        click.echo(f"No data for {dataset}; run ingest first.")
        return
    cfg = load_config()
    report = Validator(cfg.quality).validate(dataset, read_parquet(pq))
    click.echo(json.dumps(report.__dict__, indent=2, default=str))


@cli.command("status")
def status() -> None:
    cfg = load_config()
    pipe = Pipeline()
    click.echo("World Bank Data Platform — status")
    click.echo(f"Base URL: {cfg.worldbank.base_url}")
    click.echo(f"Connectors: {', '.join(registered_connectors())}")
    for name, spec in cfg.sources.items():
        pq = pipe.latest_parquet(name)
        have = f"{len(read_parquet(pq))} rows" if pq else "no data"
        click.echo(f"  {name}: enabled={spec.enabled} -> {have}")
    click.echo(f"Sheet: {cfg.sheets.spreadsheet_id or '(not configured)'}")


if __name__ == "__main__":
    cli()
