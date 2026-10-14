"""Command-line entry point."""
import argparse
import sys

from .monitor import load_config, run_checks, write_csv_report, write_json_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor HTTP endpoint health and response times.")
    parser.add_argument("-c", "--config", default="config/endpoints.json", help="Path to endpoint JSON config")
    parser.add_argument("--timeout", type=float, default=5.0, help="Request timeout in seconds")
    parser.add_argument("--expected-status", type=int, default=200, help="HTTP status considered healthy")
    parser.add_argument("--json", dest="json_path", default="reports/health-report.json", help="JSON output path")
    parser.add_argument("--csv", dest="csv_path", default="reports/health-report.csv", help="CSV output path")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    if not 100 <= args.expected_status <= 599:
        parser.error("--expected-status must be between 100 and 599")

    try:
        config = load_config(args.config)
    except (OSError, ValueError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    results = run_checks(config["endpoints"], timeout=args.timeout,
                         expected_status=args.expected_status)
    print("\nAPI Health Monitor\n" + "=" * 68)
    for item in results:
        label = "UP" if item.healthy else "DOWN"
        status = str(item.status_code) if item.status_code is not None else "n/a"
        latency = f"{item.response_time_ms:.2f} ms" if item.response_time_ms is not None else "n/a"
        print(f"[{label:4}] {item.name:<25} HTTP {status:<4} {latency:>12}")
        if item.error:
            print(f"       {item.error}")
    healthy = sum(item.healthy for item in results)
    print("-" * 68 + f"\nHealthy: {healthy}/{len(results)}")
    try:
        write_json_report(results, args.json_path)
        write_csv_report(results, args.csv_path)
    except OSError as exc:
        print(f"Report error: {exc}", file=sys.stderr)
        return 2
    print(f"JSON report: {args.json_path}\nCSV report:  {args.csv_path}")
    return 0 if healthy == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
