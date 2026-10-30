"""Retry policy for transient API health-check failures."""
from __future__ import annotations

import time
from dataclasses import replace
from time import perf_counter

from .monitor import CheckResult, check_endpoint


def check_with_retries(
    endpoint: dict[str, str],
    *,
    timeout: float = 5.0,
    expected_status: int = 200,
    retries: int = 2,
    retry_delay: float = 0.5,
) -> CheckResult:
    """Retry network errors and HTTP 5xx responses with exponential backoff."""
    if retries < 0 or retry_delay < 0:
        raise ValueError("retries and retry_delay cannot be negative")

    endpoint_expected_status = endpoint.get("expected_status", expected_status)
    if isinstance(endpoint_expected_status, bool) or not isinstance(endpoint_expected_status, int) or not 100 <= endpoint_expected_status <= 599:
        raise ValueError("endpoint expected_status must be an integer between 100 and 599")

    started = perf_counter()
    result: CheckResult | None = None
    for attempt in range(retries + 1):
        result = check_endpoint(endpoint, timeout=timeout, expected_status=endpoint_expected_status)
        invalid_url = (result.error or "").startswith("URL must start with http:// or https://")
        transient = (result.status_code is None and not invalid_url) or (
            result.status_code is not None and 500 <= result.status_code <= 599
        )
        if result.healthy or not transient or attempt == retries:
            elapsed_ms = round((perf_counter() - started) * 1000, 2)
            return replace(result, attempts=attempt + 1, total_duration_ms=elapsed_ms)
        if retry_delay:
            time.sleep(retry_delay * (2 ** attempt))

    raise RuntimeError("Unexpected retry loop exit")


def run_checks_with_retries(
    endpoints: list[dict[str, str]],
    *,
    timeout: float = 5.0,
    expected_status: int = 200,
    retries: int = 2,
    retry_delay: float = 0.5,
) -> list[CheckResult]:
    """Check endpoints in configuration order using the retry policy."""
    return [
        check_with_retries(
            endpoint,
            timeout=timeout,
            expected_status=expected_status,
            retries=retries,
            retry_delay=retry_delay,
        )
        for endpoint in endpoints
    ]
