"""Retry policy: exponential backoff via tenacity, driven by config."""
from __future__ import annotations

import logging
from typing import Any, Callable

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

log = logging.getLogger("worldbank.ingestion.retry")

RETRYABLE = (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError)
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _retryable_response(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
        return exc.response.status_code in RETRYABLE_STATUS
    return isinstance(exc, RETRYABLE)


def make_retry(max_attempts: int = 4, base: float = 2.0,
               multiplier: float = 2.0, maximum: float = 60.0) -> Callable:
    """Build a tenacity retry decorator: 2s -> 4s -> 8s ... (configurable)."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=multiplier, min=base, max=maximum),
        retry=retry_if_exception_type((httpx.HTTPError,)),
        before_sleep=before_sleep_log(log, logging.WARNING),
        reraise=True,
    )


def is_retryable(exc: BaseException) -> bool:
    return _retryable_response(exc)
