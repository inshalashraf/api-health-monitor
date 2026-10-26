"""Simple, testable scheduling for repeated monitoring cycles."""
from collections.abc import Callable
import time


def run_periodically(
    run_once: Callable[[], int],
    *,
    interval_seconds: float,
    max_runs: int | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    """Run a monitoring cycle repeatedly and return the most important exit status.

    Exit status 2 (configuration/reporting error) takes precedence over health
    failures (1). A max_runs value of None runs until interrupted by the caller.
    """
    if interval_seconds < 0:
        raise ValueError("interval_seconds cannot be negative")
    if max_runs is not None and max_runs < 1:
        raise ValueError("max_runs must be at least 1 when provided")
    if max_runs is None and interval_seconds <= 0:
        raise ValueError("an infinite schedule requires a positive interval")

    runs = 0
    overall_status = 0
    while max_runs is None or runs < max_runs:
        status = run_once()
        runs += 1
        if status == 2:
            overall_status = 2
        elif status == 1 and overall_status == 0:
            overall_status = 1
        if max_runs is not None and runs >= max_runs:
            break
        sleep(interval_seconds)
    return overall_status
