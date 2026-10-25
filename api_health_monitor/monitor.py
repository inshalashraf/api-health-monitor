"""Endpoint checks and report writers for API Health Monitor."""
from __future__ import annotations

import csv
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class CheckResult:
    """Health-check result for one endpoint."""
    name: str
    url: str
    checked_at: str
    status_code: int | None
    response_time_ms: float | None
    healthy: bool
    error: str | None = None
    attempts: int = 1
    total_duration_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check_endpoint(endpoint: dict[str, str], *, timeout: float = 5.0,
                   expected_status: int = 200) -> CheckResult:
    """Perform a GET request and measure elapsed time."""
    name = endpoint.get("name") or endpoint.get("url") or "unnamed"
    url = endpoint.get("url", "")
    checked_at = datetime.now(timezone.utc).isoformat()
    if not url.startswith(("https://", "http://")):
        return CheckResult(name, url, checked_at, None, None, False,
                           "URL must start with http:// or https://")

    request = Request(url, headers={"User-Agent": "api-health-monitor/1.0"}, method="GET")
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.getcode()
            response.read(1)
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        healthy = status == expected_status
        error = None if healthy else f"Expected HTTP {expected_status}, received {status}"
        return CheckResult(name, url, checked_at, status, elapsed, healthy, error, total_duration_ms=elapsed)
    except HTTPError as exc:
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        healthy = exc.code == expected_status
        error = None if healthy else f"Expected HTTP {expected_status}, received {exc.code}"
        return CheckResult(name, url, checked_at, exc.code, elapsed, healthy, error, total_duration_ms=elapsed)
    except (URLError, TimeoutError, OSError) as exc:
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        reason = getattr(exc, "reason", exc)
        return CheckResult(name, url, checked_at, None, elapsed, False, str(reason), total_duration_ms=elapsed)


def load_config(path: str | Path) -> dict[str, Any]:
    """Load and validate endpoint configuration from JSON."""
    with Path(path).open(encoding="utf-8") as handle:
        config = json.load(handle)
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a JSON object")
    endpoints = config.get("endpoints")
    if not isinstance(endpoints, list) or not endpoints:
        raise ValueError("Configuration must contain a non-empty endpoints list")
    for index, endpoint in enumerate(endpoints):
        if not isinstance(endpoint, dict) or not isinstance(endpoint.get("url"), str):
            raise ValueError(f"Endpoint at index {index} must include a URL string")
    return config


def run_checks(endpoints: list[dict[str, str]], *, timeout: float = 5.0,
               expected_status: int = 200) -> list[CheckResult]:
    """Check endpoints in configuration order."""
    return [check_endpoint(item, timeout=timeout, expected_status=expected_status)
            for item in endpoints]


def _summary(results: list[CheckResult]) -> dict[str, int]:
    healthy = sum(item.healthy for item in results)
    return {"total": len(results), "healthy": healthy, "unhealthy": len(results) - healthy}


def write_json_report(results: list[CheckResult], path: str | Path) -> None:
    """Write a timestamped JSON report and aggregate counts."""
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(),
               "summary": _summary(results),
               "results": [item.to_dict() for item in results]}
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv_report(results: list[CheckResult], path: str | Path) -> None:
    """Write individual check results to CSV."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fields = list(CheckResult.__dataclass_fields__)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(item.to_dict() for item in results)
