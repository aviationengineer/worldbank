"""Connector architecture: implement BaseConnector to add a new API."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterator

from ..config.models import AppConfig


@dataclass
class ConnectorResult:
    source: str
    endpoint: str
    records: list[dict[str, Any]] = field(default_factory=list)
    raw_pages: list[Any] = field(default_factory=list)


class BaseConnector(ABC):
    """Contract every API connector fulfills. Registry wires names -> classes."""

    name: str = "base"

    def __init__(self, config: AppConfig):
        self.config = config

    @abstractmethod
    def fetch(self, **kwargs: Any) -> Iterator[ConnectorResult]:
        """Yield ConnectorResult batches (one per logical request)."""
        raise NotImplementedError

    def dataset_name(self) -> str:
        return self.name


_REGISTRY: dict[str, type[BaseConnector]] = {}


def register(name: str):
    def deco(cls: type[BaseConnector]) -> type[BaseConnector]:
        cls.name = name
        _REGISTRY[name] = cls
        return cls
    return deco


def get_connector(name: str, config: AppConfig) -> BaseConnector:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown connector '{name}'. Registered: {sorted(_REGISTRY)}")
    return _REGISTRY[name](config)


def registered_connectors() -> list[str]:
    return sorted(_REGISTRY)
