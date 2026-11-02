"""Connector package.

Importing this package imports every connector module, which runs their
@register decorators and populates the connector registry.
"""
from . import (  # noqa: F401  (import order: base client first, then connectors)
    worldbank,
    indicators,
    countries,
    projects,
    finance,
    poverty,
    climate,
    documents,
    catalog,
    sdmx,
)
from .base import (  # noqa: F401
    BaseConnector,
    ConnectorResult,
    get_connector,
    register,
    registered_connectors,
)
