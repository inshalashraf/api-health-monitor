"""Command-line entry point."""
import argparse
import sys

from .history import append_history, read_history, summarize_history
from .monitor import load_config, write_csv_report, write_json_report
from .retry import run_checks_with_retries
from .scheduler import run_periodically


def run_once(args) -> int:
    """Execute one monitoring cycle, persist its reports, and print a summary."""
    try:
        config = load_config(args.config)
        history_records = read_history(args.history)
    except (OSError, ValueError) as exc:
        print(f"Configuration/history error: {exc}", file=sys.stderr)
        return 2

    results = run_checks_with_retries(
        config["endpoints"], timeout=args.timeout,
        expected_status=args.expected_status,
        retries=args.retries, retry_delay=args.retry_delay,
    )
    print("\nAPI Health Monitor\n" + "=" * 68)
    for item in results:
        label = "UP" if item.healthy else "DOWN"
        status = str(item.status_code) if item.status_code is not None else "n/a"
        latency = f"{item.response_time_ms:.2f} ms" if item.response_time_ms is not None else "n/a"
        total = f"{item.total_duration_ms:.2f} ms" if item.total_duration_ms is not None else "n/a"
        attempts = f"{item.attempts} attempt" + ("" if item.attempts == 1 else "s")
        print(f"[{label:4}] {item.name:<25} HTTP {status:<4} latency={latency:>10} total={total:>10} ({attempts})")
        if item.error:
            print(f"       {item.error}")
    healthy = sum(item.healthy for item in results)
    print("-" * 68 + f"\nHealthy: {healthy}/{len(results)}")

    try:
        write_json_report(results, args.json_path)
        write_csv_report(results, args.csv_path)
        history_records.extend(append_history(results, args.history))
    except OSError as exc:
        print(f"Report/history error: {exc}", file=sys.stderr)
        return 2

    print(f"JSON report: {args.json_path}\nCSV report:  {args.csv_path}")
    print(f"History:     {args.history}")
    print("Historical uptime (all recorded checks):")
    for summary in summarize_history(history_records):
        average = summary["average_response_time_ms"]
        latency_text = f"{average:.2f} ms" if average is not None else "n/a"
        print(
            f"  {summary['name']}: {summary['uptime_percentage']:.2f}% "
            f"({summary['healthy']}/{summary['checks']} checks), "
            f"average latency {latency_text}"
        )
    return 0 if healthy == len(results) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor HTTP endpoint health and response times.")
    parser.add_argument("-c", "--config", default="config/endpoints.json", help="Path to endpoint JSON config")
    parser.add_argument("--timeout", type=float, default=5.0, help="Request timeout in seconds")
    parser.add_argument("--expected-status", type=int, default=200, help="HTTP status considered healthy")
    parser.add_argument("--retries", type=int, default=2, help="Retries for network errors and HTTP 5xx responses")
    parser.add_argument("--retry-delay", type=float, default=0.5, help="Initial retry delay in seconds; doubles after each attempt")
    parser.add_argument("--json", dest="json_path", default="reports/health-report.json", help="JSON output path")
    parser.add_argument("--csv", dest="csv_path", default="reports/health-report.csv", help="CSV output path")
    parser.add_argument("--history", default="reports/history.jsonl", help="Append-only JSONL history path")
    parser.add_argument("--interval", type=float, default=0, help="Seconds between cycles; 0 runs once (default: 0)")
    parser.add_argument("--max-runs", type=int, default=None, help="Stop after this many cycles; omit for continuous monitoring")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    if not 100 <= args.expected_status <= 599:
        parser.error("--expected-status must be between 100 and 599")
    if args.retries < 0:
        parser.error("--retries cannot be negative")
    if args.retry_delay < 0:
        parser.error("--retry-delay cannot be negative")
    if args.interval < 0:
        parser.error("--interval cannot be negative")
    if args.max_runs is not None and args.max_runs < 1:
        parser.error("--max-runs must be at least 1")
    if args.interval == 0 and args.max_runs is None:
        args.max_runs = 1
    if args.max_runs is None and args.interval <= 0:
        parser.error("continuous monitoring requires --interval greater than zero")

    if args.max_runs is None:
        print(f"Continuous monitoring every {args.interval:g}s. Press Ctrl+C to stop.")
    elif args.max_runs > 1:
        print(f"Running {args.max_runs} monitoring cycles every {args.interval:g}s.")

    try:
        return run_periodically(
            lambda: run_once(args),
            interval_seconds=args.interval,
            max_runs=args.max_runs,
        )
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
