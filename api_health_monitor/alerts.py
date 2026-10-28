"""Webhook notifications for unhealthy monitoring results."""
import json
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def build_alert_payload(results):
    """Build a compact JSON-serializable alert for unhealthy endpoints."""
    unhealthy = [item for item in results if not item.healthy]
    return {
        "event": "api_health_alert",
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": len(results),
            "healthy": len(results) - len(unhealthy),
            "unhealthy": len(unhealthy),
        },
        "unhealthy_endpoints": [
            {
                "name": item.name,
                "url": item.url,
                "checked_at": item.checked_at,
                "status_code": item.status_code,
                "response_time_ms": item.response_time_ms,
                "attempts": item.attempts,
                "error": item.error,
            }
            for item in unhealthy
        ],
    }


def send_webhook_alert(results, webhook_url, *, timeout=5.0):
    """Send an alert when at least one endpoint is unhealthy.

    Returns None when no alert is needed or delivery succeeds, otherwise a
    human-readable error. The webhook URL is deliberately never included in
    returned errors because it may contain a secret token.
    """
    if not webhook_url:
        return None
    if not webhook_url.startswith(("https://", "http://")):
        return "Webhook URL must start with http:// or https://"
    unhealthy = [item for item in results if not item.healthy]
    if not unhealthy:
        return None

    body = json.dumps(build_alert_payload(results)).encode("utf-8")
    request = Request(
        webhook_url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "api-health-monitor/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.getcode()
        if not 200 <= status < 300:
            return f"Webhook returned HTTP {status}"
    except HTTPError as exc:
        return f"Webhook returned HTTP {exc.code}"
    except (URLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        return f"Webhook delivery failed: {reason}"
    return None
