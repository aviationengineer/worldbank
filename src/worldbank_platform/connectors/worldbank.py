"""World Bank v2 HTTP client: pagination, retries, rate-limit handling."""
from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx

from ..config.models import AppConfig, HttpSettings
from ..ingestion.paginator import Paginator
from ..ingestion.retry import make_retry

log = logging.getLogger("worldbank.connector")


class WorldBankError(RuntimeError):
    pass


def _ca_bundle(http_cfg) -> str | bool:
    """TLS bundle: explicit config, else SSL_CERT_FILE (corporate egress proxies)."""
    return http_cfg.ca_bundle or os.environ.get("SSL_CERT_FILE") or True


def _proxy_url() -> str | None:
    """Explicit egress proxy from the environment (deterministic; avoids
    httpx's no_proxy parsing quirks with bracketed IPv6 literals)."""
    return os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")


class WorldBankClient:
    """Thin client over https://api.worldbank.org/v2 (public, no key required)."""

    def __init__(self, config: AppConfig, http: httpx.Client | None = None):
        self.base_url = config.worldbank.base_url.rstrip("/")
        self.per_page = config.worldbank.per_page
        self.http_cfg: HttpSettings = config.http
        self._client = http or httpx.Client(
            timeout=config.worldbank.timeout_seconds,
            headers={"User-Agent": "worldbank-data-platform/0.1.0"},
            proxy=_proxy_url(),
            trust_env=False,
            verify=_ca_bundle(self.http_cfg),
        )
        self._get = make_retry(
            max_attempts=self.http_cfg.max_attempts,
            base=self.http_cfg.backoff_base_seconds,
            multiplier=self.http_cfg.backoff_multiplier,
            maximum=self.http_cfg.max_backoff_seconds,
        )(self._get_once)

    def _get_once(self, path: str, params: dict[str, Any]) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        resp = self._client.get(url, params=params)
        if resp.status_code == 429 and self.http_cfg.respect_retry_after:
            wait = float(resp.headers.get("Retry-After", "5"))
            log.warning("Rate limited; sleeping %.1fs", wait)
            time.sleep(min(wait, 60))
        resp.raise_for_status()
        try:
            return resp.json()
        except ValueError as exc:
            raise WorldBankError(f"Non-JSON response from {url}") from exc

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._get(path, dict(params or {}))

    def paged(self, path: str, params: dict[str, Any] | None = None):
        """Yield (items, total_pages, total) handling World Bank's [meta, data] envelope."""
        base = dict(params or {})
        base.setdefault("format", "json")
        base.setdefault("per_page", self.per_page)

        def fetch_page(page: int) -> tuple[list[dict], int, int]:
            payload = self.get(path, {**base, "page": page})
            if not isinstance(payload, list) or len(payload) != 2:
                # error envelope, e.g. [{"message": [...]}]
                raise WorldBankError(f"Unexpected envelope from {path}: {str(payload)[:200]}")
            meta, data = payload
            total_pages = int(meta.get("pages", 1) or 1)
            total = int(meta.get("total", 0) or 0)
            return (data or []), total_pages, total

        return Paginator(fetch_page=fetch_page)

    def close(self) -> None:
        self._client.close()
