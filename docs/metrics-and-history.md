# Health-check metrics and history

This project reports three different views of a check:

- `response_time_ms` measures the final HTTP request. It does not include time spent waiting between retries.
- `total_duration_ms` measures the complete check, including every attempt and exponential-backoff delay.
- `attempts` counts the HTTP/network attempts made for the endpoint.

The JSONL history stores one record per endpoint check. Historical uptime is the percentage of recorded checks marked healthy; it is an all-time value for the selected history file, not a rolling window. Average response latency excludes checks whose latency could not be measured (for example, an invalid URL). A missing history file is treated as an empty history, while malformed records are rejected with a line number so the data can be repaired instead of silently ignored.

## Reproducible local check

Run the unit suite with:

```bash
python -m unittest discover -s tests -v
```

Use a separate `--history` path when you want to isolate a test run from production history. Only monitor endpoints you own or are authorized to check.
