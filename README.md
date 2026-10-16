# API Health Monitor

A lightweight, dependency-free Python command-line tool that checks HTTP endpoint availability, measures response times, and exports JSON and CSV reports.

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

`--config` chooses the JSON config, `--timeout` sets seconds per request, `--expected-status` sets the healthy HTTP status, `--retries` sets the number of retries (default: 2), `--retry-delay` sets the initial backoff delay in seconds (default: 0.5), and `--json` and `--csv` choose report paths. Exit codes: 0 when all endpoints are healthy, 1 when checks fail, 2 on configuration/report errors. Only monitor endpoints you own or are authorized to check.

## Features

- HTTP status and per-request latency checks
- Attempt counts and total check duration, including retry delays
- Timeout, DNS, connection, and HTTP error reporting
- Configurable healthy status code
- Exponential-backoff retries for network failures and HTTP 5xx responses; 4xx responses are not retried
- Timestamped JSON summary and CSV reports
- Standard-library unit tests; no runtime dependencies

Checks run sequentially. `response_time_ms` records the final request's latency; `total_duration_ms` includes all attempts and backoff delays. JSON and CSV reports include the attempt count and total duration. Continuous scheduling, authentication, and alert delivery remain future improvements.
