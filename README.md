# API Health Monitor

A lightweight, dependency-free Python command-line tool that checks HTTP endpoint availability, measures response times, and exports JSON, CSV, and persistent history.

## Quick start

```bash
git clone https://github.com/inshalashraf/api-health-monitor.git
cd api-health-monitor
python -m api_health_monitor.cli
```

Requirements: Python 3.10+. Edit `config/endpoints.json` to configure endpoints. Use `python -m unittest discover -s tests -v` to run the tests.

## Options

```bash
python -m api_health_monitor.cli --help
```

`--config` chooses the JSON config, `--timeout` sets seconds per request, `--expected-status` sets the healthy HTTP status, `--retries` sets the number of retries (default: 2), `--retry-delay` sets the initial backoff delay in seconds (default: 0.5), `--json` and `--csv` choose report paths, and `--history` chooses the persistent JSONL history file (default: `reports/history.jsonl`). Exit codes: 0 when all endpoints are healthy, 1 when checks fail, 2 on configuration/report/history errors. Only monitor endpoints you own or are authorized to check.

## Features

- HTTP status and per-request latency checks
- Attempt counts and total check duration, including retry delays
- Timeout, DNS, connection, and HTTP error reporting
- Configurable healthy status code
- Exponential-backoff retries for network failures and HTTP 5xx responses; 4xx responses are not retried
- Timestamped JSON summary and CSV reports
- Append-only JSON Lines history across runs, with all-time uptime percentage and average measured latency per endpoint
- Validates history records and reports malformed JSONL with a line number
- Standard-library unit tests; no runtime dependencies

Checks run sequentially. `response_time_ms` records the final request's latency; `total_duration_ms` includes all attempts and backoff delays. JSON and CSV reports include attempt count and total duration. The history file is append-only; choose another path with `--history` to start a separate history, or remove the file to reset it. Continuous scheduling, authentication, and alert delivery remain future improvements.
