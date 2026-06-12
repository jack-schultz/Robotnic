from dataclasses import dataclass, field
import threading


@dataclass
class BotStats:
    guilds: int = 0
    users: int = 0

    lock: threading.Lock = field(default_factory=threading.Lock)


stats = BotStats()
