"""Tests for webhook alert payloads and delivery."""
import json
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import URLError

from api_health_monitor.alerts import build_alert_payload, send_webhook_alert
from api_health_monitor.monitor import CheckResult


class WebhookAlertTests(unittest.TestCase):
    def setUp(self):
        self.healthy = CheckResult(
            "api", "https://api.example.com", "2026-01-01T00:00:00+00:00",
            200, 12.5, True, attempts=1, total_duration_ms=12.5,
        )
        self.unhealthy = CheckResult(
            "payments", "https://payments.example.com", "2026-01-01T00:00:01+00:00",
            503, 30.0, False, "Expected HTTP 200, received 503",
            attempts=3, total_duration_ms=530.0,
        )

    def test_payload_includes_only_unhealthy_endpoints(self):
        payload = build_alert_payload([self.healthy, self.unhealthy])
        self.assertEqual(payload["event"], "api_health_alert")
        self.assertEqual(payload["summary"], {"total": 2, "healthy": 1, "unhealthy": 1})
        self.assertEqual([item["name"] for item in payload["unhealthy_endpoints"]], ["payments"])
        self.assertEqual(payload["unhealthy_endpoints"][0]["attempts"], 3)

    @patch("api_health_monitor.alerts.urlopen")
    def test_sends_json_post_for_unhealthy_endpoint(self, urlopen):
        response = MagicMock()
        response.getcode.return_value = 200
        urlopen.return_value.__enter__.return_value = response
        result = send_webhook_alert([self.healthy, self.unhealthy], "https://hooks.example.com/secret")
        self.assertIsNone(result)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Content-type"), "application/json")
        payload = json.loads(request.data)
        self.assertEqual(payload["summary"]["unhealthy"], 1)

    @patch("api_health_monitor.alerts.urlopen")
    def test_does_not_send_when_all_healthy(self, urlopen):
        self.assertIsNone(send_webhook_alert([self.healthy], "https://hooks.example.com"))
        urlopen.assert_not_called()

    @patch("api_health_monitor.alerts.urlopen", side_effect=URLError("offline"))
    def test_delivery_error_does_not_expose_webhook_url(self, _urlopen):
        secret_url = "https://hooks.example.com/token-secret"
        error = send_webhook_alert([self.unhealthy], secret_url)
        self.assertIn("Webhook delivery failed", error)
        self.assertNotIn("token-secret", error)

    def test_rejects_non_http_webhook_url(self):
        self.assertIn("must start", send_webhook_alert([self.unhealthy], "file:///tmp/hook"))

    @patch("api_health_monitor.alerts.urlopen")
    def test_reports_http_error(self, urlopen):
        from urllib.error import HTTPError
        urlopen.side_effect = HTTPError("https://hooks.example.com", 429, "rate limit", {}, None)
        self.assertEqual(
            send_webhook_alert([self.unhealthy], "https://hooks.example.com"),
            "Webhook returned HTTP 429",
        )


if __name__ == "__main__":
    unittest.main()
