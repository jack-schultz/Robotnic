from dataclasses import dataclass, field
import threading


@dataclass
class BotStats:
    guilds: int = 0
    users: int = 0
    creators: int = 0
    channels: int = 0
    connected_users: int = 0

    lock: threading.Lock = field(default_factory=threading.Lock)


stats = BotStats()


STATS_FIELDS = ["guilds", "users", "creators", "channels", "connected_users"]


def read_stats_history(days=None, interval=None):
    """Read logs/stats.csv; optionally limit to the last `days` and keep the last row per `interval` seconds."""
    import csv
    from datetime import datetime, timedelta, timezone
    from config.paths import STATS_LOG_PATH

    rows = []
    if not STATS_LOG_PATH.exists():
        return {"fields": STATS_FIELDS, "rows": rows}

    cutoff = datetime.now(timezone.utc) - timedelta(days=days) if days else None
    last_bucket = None
    with STATS_LOG_PATH.open(newline="", encoding="utf-8") as f:
        for rec in csv.DictReader(f):
            try:
                ts = datetime.fromisoformat(rec["timestamp"])
                values = [int(rec[k]) for k in STATS_FIELDS]
            except (KeyError, TypeError, ValueError):
                continue  # malformed or partially written row
            if cutoff and ts < cutoff:
                continue
            if interval:
                bucket = int(ts.timestamp()) // interval
                if bucket == last_bucket and rows:
                    rows.pop()  # keep the last row in each bucket
                last_bucket = bucket
            rows.append([ts.isoformat(timespec="seconds"), *values])
    return {"fields": STATS_FIELDS, "rows": rows}
