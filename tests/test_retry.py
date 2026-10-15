"""Tests for transient-failure retry behavior."""
import unittest
from unittest.mock import patch

from api_health_monitor.monitor import CheckResult
from api_health_monitor.retry import check_with_retries


class RetryTests(unittest.TestCase):
    def setUp(self):
        self.endpoint = {"name": "sample", "url": "https://example.com"}
        self.failed_network = CheckResult(
            "sample", "https://example.com", "now", None, 2.0, False, "offline"
        )
        self.failed_server = CheckResult(
            "sample", "https://example.com", "now", 503, 2.0, False,
            "Expected HTTP 200, received 503"
        )
        self.healthy = CheckResult(
            "sample", "https://example.com", "now", 200, 2.0, True
        )

    @patch("api_health_monitor.retry.time.sleep")
    @patch("api_health_monitor.retry.check_endpoint")
    def test_retries_network_error_then_succeeds(self, check, sleep):
        check.side_effect = [self.failed_network, self.healthy]
        result = check_with_retries(self.endpoint, retries=1, retry_delay=0.25)
        self.assertTrue(result.healthy)
        self.assertEqual(check.call_count, 2)
        sleep.assert_called_once_with(0.25)

    @patch("api_health_monitor.retry.time.sleep")
    @patch("api_health_monitor.retry.check_endpoint")
    def test_retries_http_5xx_then_succeeds(self, check, sleep):
        check.side_effect = [self.failed_server, self.healthy]
        result = check_with_retries(self.endpoint, retries=1, retry_delay=0)
        self.assertTrue(result.healthy)
        self.assertEqual(check.call_count, 2)
        sleep.assert_not_called()

    @patch("api_health_monitor.retry.check_endpoint")
    def test_does_not_retry_client_error(self, check):
        client_error = CheckResult(
            "sample", "https://example.com", "now", 404, 1.0, False,
            "Expected HTTP 200, received 404"
        )
        check.return_value = client_error
        result = check_with_retries(self.endpoint, retries=3, retry_delay=0)
        self.assertEqual(result.status_code, 404)
        check.assert_called_once()

    @patch("api_health_monitor.retry.check_endpoint")
    def test_does_not_retry_invalid_url(self, check):
        invalid = CheckResult(
            "sample", "file:///tmp/test", "now", None, None, False,
            "URL must start with http:// or https://"
        )
        check.return_value = invalid
        result = check_with_retries(
            {"name": "invalid", "url": "file:///tmp/test"}, retries=3, retry_delay=0
        )
        self.assertFalse(result.healthy)
        check.assert_called_once()

    def test_negative_retry_count_is_rejected(self):
        with self.assertRaises(ValueError):
            check_with_retries(self.endpoint, retries=-1)

    def test_negative_retry_delay_is_rejected(self):
        with self.assertRaises(ValueError):
            check_with_retries(self.endpoint, retry_delay=-0.1)


if __name__ == "__main__":
    unittest.main()
