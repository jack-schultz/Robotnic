import asyncio
import logging
from cogs.control_vc.embed_updates import edit_info_embed

logger = logging.getLogger(__name__)


class EmbedUpdateScheduler:
    def __init__(self, bot, debounce_seconds=2.5, max_concurrent=4):
        self.bot = bot
        self.debounce_seconds = debounce_seconds
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.pending = {}
        self.workers = {}
        self.stats = {"scheduled": 0, "skipped": 0, "edited": 0, "rate_limited": 0}

    async def schedule(self, channel, *, title=None, user_limit=None):
        channel_id = channel.id
        pending = self.pending.setdefault(channel_id, {})
        if title is not None:
            pending["title"] = title
        if user_limit is not None:
            pending["user_limit"] = user_limit
        self.stats["scheduled"] += 1

        worker = self.workers.get(channel_id)
        if worker is None or worker.done():
            self.workers[channel_id] = asyncio.create_task(self._worker(channel_id))

    async def _worker(self, channel_id):
        try:
            while channel_id in self.pending:
                await asyncio.sleep(self.debounce_seconds)

                kwargs = self.pending.pop(channel_id, None)
                if kwargs is None:
                    break

                channel = self.bot.get_channel(channel_id)
                if channel is None:
                    if self.bot.repos.temp_channels.get_info(channel_id) is not None:
                        logger.debug(
                            f"Removing stale temp channel {channel_id} during embed update (channel gone)"
                        )
                        self.bot.repos.temp_channels.remove(channel_id)
                    break

                async with self.semaphore:
                    while True:
                        result = await edit_info_embed(self.bot, channel, **kwargs)
                        if result == "edited":
                            self.stats["edited"] += 1
                            break
                        if result == "skipped":
                            self.stats["skipped"] += 1
                            break
                        if result == "not_found":
                            break
                        if result == "rate_limited":
                            self.stats["rate_limited"] += 1
                            continue
                        break

                if channel_id not in self.pending:
                    break
        finally:
            self.workers.pop(channel_id, None)
            self.pending.pop(channel_id, None)
