"""Tests for persistent JSONL history and uptime summaries."""
import tempfile
import unittest
from pathlib import Path

from api_health_monitor.history import append_history, read_history, summarize_history
from api_health_monitor.monitor import CheckResult


class HistoryTests(unittest.TestCase):
    def make_result(self, *, healthy=True, latency=100.0, url="https://example.com", name="sample"):
        return CheckResult(
            name, url, "2026-10-17T10:00:00+00:00", 200 if healthy else 503,
            latency, healthy, None if healthy else "server unavailable",
        )

    def test_missing_history_is_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(read_history(Path(directory) / "missing.jsonl"), [])

    def test_history_appends_across_runs_and_summarizes_uptime(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reports" / "history.jsonl"
            append_history([self.make_result(healthy=True, latency=100.0)], path)
            append_history([self.make_result(healthy=False, latency=200.0)], path)

            records = read_history(path)
            self.assertEqual(len(records), 2)
            self.assertIn("recorded_at", records[0])
            summary = summarize_history(records)[0]
            self.assertEqual(summary["checks"], 2)
            self.assertEqual(summary["healthy"], 1)
            self.assertEqual(summary["unhealthy"], 1)
            self.assertEqual(summary["uptime_percentage"], 50.0)
            self.assertEqual(summary["average_response_time_ms"], 150.0)

    def test_summary_groups_endpoints_by_url(self):
        records = []
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.jsonl"
            append_history([
                self.make_result(url="https://one.example"),
                self.make_result(url="https://two.example"),
            ], path)
            records = read_history(path)
        self.assertEqual({item["url"] for item in summarize_history(records)}, {
            "https://one.example", "https://two.example"
        })

    def test_malformed_json_reports_line_number(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.jsonl"
            path.write_text('not-json\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "line 1"):
                read_history(path)

    def test_invalid_record_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.jsonl"
            path.write_text('{"result":{"url":"https://example.com","healthy":"yes"}}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "line 1"):
                read_history(path)

    def test_latency_is_none_when_no_requests_have_a_measurement(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.jsonl"
            append_history([self.make_result(healthy=False, latency=None)], path)
            summary = summarize_history(read_history(path))[0]
            self.assertIsNone(summary["average_response_time_ms"])


if __name__ == "__main__":
    unittest.main()
