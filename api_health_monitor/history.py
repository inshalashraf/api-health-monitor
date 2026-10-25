"""Persistent JSONL health-check history."""
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def append_history(results, path):
    """Append one record per endpoint check and return the records."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    records = [
        {"recorded_at": datetime.now(timezone.utc).isoformat(), "result": item.to_dict()}
        for item in results
    ]
    with target.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")
    return records


def read_history(path):
    """Read JSON Lines history; a missing file represents an empty history."""
    target = Path(path)
    if not target.exists():
        return []
    records = []
    with target.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid history JSON on line {line_number}") from exc
            result = record.get("result") if isinstance(record, dict) else None
            if not isinstance(result, dict) or not isinstance(result.get("url"), str) or not isinstance(result.get("healthy"), bool):
                raise ValueError(f"Invalid history record on line {line_number}")
            latency = result.get("response_time_ms")
            if latency is not None and (
                isinstance(latency, bool) or not isinstance(latency, (int, float)) or latency < 0
            ):
                raise ValueError(f"Invalid response latency on history line {line_number}")
            records.append(record)
    return records


def summarize_history(records):
    """Calculate all-time uptime and average measured latency by endpoint URL."""
    grouped = defaultdict(list)
    for record in records:
        grouped[record["result"]["url"]].append(record["result"])
    summaries = []
    for url, results in sorted(grouped.items()):
        healthy = sum(item["healthy"] for item in results)
        latencies = [item["response_time_ms"] for item in results if item.get("response_time_ms") is not None]
        summaries.append({
            "name": results[-1].get("name") or url,
            "url": url,
            "checks": len(results),
            "healthy": healthy,
            "unhealthy": len(results) - healthy,
            "uptime_percentage": round(healthy / len(results) * 100, 2),
            "average_response_time_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,
        })
    return summaries
