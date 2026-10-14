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

`--config` chooses the JSON config, `--timeout` sets seconds per request, `--expected-status` sets the healthy HTTP status, `--json` and `--csv` choose report paths. Exit codes: 0 when all endpoints are healthy, 1 when checks fail, 2 on configuration/report errors. Only monitor endpoints you own or are authorized to check.

## Features

- HTTP status and response-latency checks
- Timeout, DNS, connection, and HTTP error reporting
- Configurable healthy status code
- Timestamped JSON summary and CSV reports
- Standard-library unit tests; no runtime dependencies

Checks run sequentially. Continuous scheduling, authentication, retries, and alerts are intentionally out of scope for this first version.
