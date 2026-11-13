"""Fetch bot stats history from the API and write it to docs/stats-history.json."""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "docs" / "stats.config.json"
HISTORY_PATH = ROOT / "docs" / "stats-history.json"


def load_stats_url() -> str:
    env_url = os.environ.get("STATS_API_URL", "").strip()
    if env_url:
        return env_url

    if not CONFIG_PATH.exists():
        print(f"Missing config: {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)

    with CONFIG_PATH.open(encoding="utf-8") as f:
        config = json.load(f)

    stats_url = config.get("statsUrl", "").strip()
    if not stats_url:
        print('"statsUrl" is not set in docs/stats.config.json', file=sys.stderr)
        sys.exit(1)

    return stats_url


def load_history_url(stats_url: str) -> str:
    env_url = os.environ.get("STATS_HISTORY_API_URL", "").strip()
    if env_url:
        return env_url
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open(encoding="utf-8") as f:
            configured = json.load(f).get("historyUrl", "").strip()
        if configured:
            return configured
    return stats_url.rstrip("/") + "/history"


def fetch_stats(stats_url: str) -> dict:
    with urlopen(stats_url, timeout=30) as response:
        return json.loads(response.read())


def main() -> None:
    history_url = load_history_url(load_stats_url()) + "?interval=3600"
    print(f"Fetching stats history from {history_url}")

    try:
        history = fetch_stats(history_url)
        fields, rows = history["fields"], history["rows"]
    except (URLError, TimeoutError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"Failed to fetch stats history: {exc}", file=sys.stderr)
        sys.exit(1)

    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fields": fields,
        "rows": rows,
        "summary": history.get("summary", {}),
    }
    HISTORY_PATH.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {len(rows):,} history rows to {HISTORY_PATH}")


if __name__ == "__main__":
    main()
