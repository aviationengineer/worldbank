"""projects connector (Phase 2) — registered stub.

Enable by implementing fetch() against the World Bank projects endpoint
and setting enabled: true in config/sources.yaml.
"""
from __future__ import annotations

from typing import Any, Iterator

from .base import BaseConnector, ConnectorResult, register


@register("projects")
class ProjectsConnector(BaseConnector):
    def fetch(self, **kwargs: Any) -> Iterator[ConnectorResult]:
        raise NotImplementedError(
            "projects connector is Phase 2: implement fetch() and enable in sources.yaml")
