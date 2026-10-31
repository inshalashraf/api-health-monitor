"""Unit tests for endpoint checks and reports."""
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from api_health_monitor.monitor import (
    CheckResult, check_endpoint, load_config, run_checks,
    write_csv_report, write_json_report,
)


class MonitorTests(unittest.TestCase):
    @patch("api_health_monitor.monitor.urlopen")
    def test_successful_endpoint(self, mocked):
        response = MagicMock()
        response.getcode.return_value = 200
        mocked.return_value.__enter__.return_value = response
        result = check_endpoint({"name": "sample", "url": "https://example.com"})
        self.assertTrue(result.healthy)
        self.assertEqual(result.status_code, 200)
        self.assertIsNotNone(result.response_time_ms)
        self.assertEqual(result.total_duration_ms, result.response_time_ms)
        self.assertEqual(result.attempts, 1)

    @patch("api_health_monitor.monitor.urlopen")
    def test_unexpected_http_status(self, mocked):
        mocked.side_effect = HTTPError("https://example.com", 503, "Unavailable", {}, None)
        result = check_endpoint({"name": "sample", "url": "https://example.com"})
        self.assertFalse(result.healthy)
        self.assertEqual(result.status_code, 503)

    @patch("api_health_monitor.monitor.urlopen", side_effect=URLError("offline"))
    def test_network_failure(self, _mocked):
        result = check_endpoint({"name": "sample", "url": "https://example.com"})
        self.assertFalse(result.healthy)
        self.assertIn("offline", result.error)

    def test_invalid_url_is_rejected(self):
        result = check_endpoint({"name": "bad", "url": "file:///etc/passwd"})
        self.assertFalse(result.healthy)
        self.assertIsNone(result.status_code)
        self.assertIn("http://", result.error)

    def test_custom_expected_status(self):
        with patch("api_health_monitor.monitor.urlopen") as mocked:
            response = MagicMock()
            response.getcode.return_value = 204
            mocked.return_value.__enter__.return_value = response
            result = check_endpoint(
                {"name": "sample", "url": "https://example.com"}, expected_status=204
            )
        self.assertTrue(result.healthy)

    def test_config_requires_endpoints(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({"endpoints": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(path)

    def test_config_rejects_invalid_latency_threshold(self):
        for value in (0, -1, True, "100", math.nan, math.inf, -math.inf):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "config.json"
                path.write_text(json.dumps({"endpoints": [
                    {"name": "sample", "url": "https://example.com", "max_response_time_ms": value}
                }]), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "max_response_time_ms"):
                    load_config(path)

    def test_direct_check_rejects_non_finite_latency_threshold(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "finite positive"):
                check_endpoint({"url": "https://example.com", "max_response_time_ms": value})

    @patch("api_health_monitor.monitor.urlopen")
    def test_slow_response_exceeds_endpoint_threshold(self, mocked):
        response = MagicMock()
        response.getcode.return_value = 200
        mocked.return_value.__enter__.return_value = response
        with patch("api_health_monitor.monitor.time.perf_counter", side_effect=[1.0, 1.2]):
            result = check_endpoint(
                {"name": "sample", "url": "https://example.com", "max_response_time_ms": 100}
            )
        self.assertFalse(result.healthy)
        self.assertIn("exceeded limit", result.error)

    def test_config_rejects_invalid_endpoint_expected_status(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({"endpoints": [
                {"name": "sample", "url": "https://example.com", "expected_status": 700}
            ]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "expected_status"):
                load_config(path)

    def test_report_generation(self):
        result = CheckResult("sample", "https://example.com", "now", 200, 1.2, True)
        with tempfile.TemporaryDirectory() as directory:
            json_path = Path(directory) / "reports" / "out.json"
            csv_path = Path(directory) / "reports" / "out.csv"
            write_json_report([result], json_path)
            write_csv_report([result], csv_path)
            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["summary"]["healthy"], 1)
            self.assertIn("response_time_ms", csv_path.read_text(encoding="utf-8"))

    def test_run_checks_preserves_order(self):
        results = run_checks([
            {"name": "a", "url": "bad"}, {"name": "b", "url": "invalid"}
        ])
        self.assertEqual([item.name for item in results], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
