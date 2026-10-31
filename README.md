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

- `--config`: JSON endpoint configuration (default: `config/endpoints.json`)
- `--timeout`: seconds per request (default: 5)
- `--expected-status`: default HTTP status considered healthy (default: 200); an endpoint can override it with `expected_status` in the JSON config
- `--retries`: retries for network errors and HTTP 5xx responses (default: 2)
- `--retry-delay`: initial exponential-backoff delay in seconds (default: 0.5)
- `--json` / `--csv`: report output paths
- `--history`: append-only JSONL history path (default: `reports/history.jsonl`)
- `--webhook-url`: optional HTTP(S) endpoint that receives a JSON alert when any monitored endpoint is unhealthy
- `--interval`: seconds between monitoring cycles; 0 runs once (default: 0)
- `--max-runs`: stop after this many cycles; omit to run continuously when an interval is set

Timing options must be finite numbers; timeout must be positive, while retry delay and interval may be zero but cannot be negative. Per-endpoint `max_response_time_ms` must also be a finite positive number.

### Run continuously

Check every 30 seconds until stopped with Ctrl+C:

```bash
python -m api_health_monitor.cli --interval 30
```

Send a JSON alert to your webhook whenever a check finds an unhealthy endpoint:

```bash
python -m api_health_monitor.cli --webhook-url https://your-webhook.example/endpoint
```

Keep webhook URLs containing tokens private; do not commit them to source control. Alerts are sent only when at least one endpoint is unhealthy. Delivery problems are printed as warnings and do not mask the monitor result.

Run exactly five cycles, 10 seconds apart:

```bash
python -m api_health_monitor.cli --interval 10 --max-runs 5
```

Reports are refreshed after each cycle, while JSONL history is appended so uptime and average latency summaries accumulate across runs. Continuous mode exits with status 1 if any cycle finds an unhealthy endpoint, and status 2 if a configuration or report/history error occurs. Only monitor endpoints you own or are authorized to check.

### Endpoint-specific success codes

Some APIs use a successful status other than 200, such as `204 No Content` for a health endpoint or `301` for a redirect-only check. Set `expected_status` on an individual endpoint; it overrides the command-line default for that endpoint:

```json
{
  "endpoints": [
    {"name": "Website", "url": "https://example.com", "expected_status": 200},
    {"name": "Readiness probe", "url": "https://api.example.com/ready", "expected_status": 204}
  ]
}
```

The value must be an integer HTTP status from 100 through 599. Endpoints without this setting continue to use `--expected-status`.

## Features

- HTTP status and per-request latency checks, with optional per-endpoint latency budgets
- Attempt counts and total check duration, including retry delays
- Timeout, DNS, connection, and HTTP error reporting
- Configurable global and per-endpoint healthy status codes
- Exponential-backoff retries for network failures and HTTP 5xx responses; 4xx responses are not retried
- Timestamped JSON summary and CSV reports
- Append-only JSON Lines history, all-time uptime percentage, and average measured latency per endpoint
- Continuous monitoring with configurable intervals and finite run limits
- Optional JSON webhook alerts for unhealthy endpoints
- Validates history records and reports malformed JSONL with a line number
- Standard-library unit tests; no runtime dependencies

Checks run sequentially. `response_time_ms` records the final request's latency; `total_duration_ms` includes all attempts and backoff delays. The history file is append-only; choose another path with `--history` to start a separate history, or remove the file to reset it. Authentication and built-in email/chat integrations remain future improvements.
