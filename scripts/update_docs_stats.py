"""Fetch bot stats from the API and write them into docs/index.html."""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "docs" / "stats.config.json"
INDEX_PATH = ROOT / "docs" / "index.html"


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


def fetch_stats(stats_url: str) -> dict:
    with urlopen(stats_url, timeout=30) as response:
        return json.loads(response.read())


def update_index(html: str, guilds: int, users: int) -> str:
    html = re.sub(
        r'(<span class="stat-card__value" id="stat-servers">)[^<]*',
        rf"\g<1>{guilds:,}",
        html,
        count=1,
    )
    html = re.sub(
        r'(<span class="stat-card__value" id="stat-users">)[^<]*',
        rf"\g<1>{users:,}",
        html,
        count=1,
    )

    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    html = re.sub(
        r'(<p class="stats__note" id="stats-updated">)[^<]*',
        rf"\g<1>Last updated: {updated}",
        html,
        count=1,
    )
    return html


def main() -> None:
    stats_url = load_stats_url()
    print(f"Fetching stats from {stats_url}")

    try:
        stats = fetch_stats(stats_url)
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"Failed to fetch stats: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        guilds = int(stats["guilds"])
        users = int(stats["users"])
    except (KeyError, TypeError, ValueError) as exc:
        print(f"Unexpected stats response: {stats!r} ({exc})", file=sys.stderr)
        sys.exit(1)

    html = INDEX_PATH.read_text(encoding="utf-8")
    INDEX_PATH.write_text(update_index(html, guilds, users), encoding="utf-8")
    print(f"Updated docs: {guilds:,} servers, {users:,} users")


if __name__ == "__main__":
    main()
