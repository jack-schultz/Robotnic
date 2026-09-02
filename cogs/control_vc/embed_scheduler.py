import asyncio
import logging
import discord
from cogs.control_vc.embeds import ChannelInfoEmbed

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


def _info_embed_signature(embed: discord.Embed) -> tuple:
    fields = tuple((field.name, field.value) for field in embed.fields)
    return (embed.title, fields)


async def schedule_info_embed(bot, channel, title=None, user_limit=None):
    await bot.EmbedUpdateScheduler.schedule(channel, title=title, user_limit=user_limit)


async def edit_info_embed(bot, channel, title=None, user_limit=None):
    """
    Edit the control message info embed. Returns:
    - "edited" | "skipped" | "not_found" | "rate_limited" | "error"
    """
    guild_name = channel.guild.name
    control_message = None
    messages = channel.history(limit=1, oldest_first=True)
    async for message in messages:
        control_message = message
    if control_message is None:
        logger.debug(
            f"No control message found for temp channel {channel.id} in guild '{guild_name}'"
        )
        return "not_found"

    if len(control_message.embeds) < 2:
        logger.warning(
            f"Control message for temp channel {channel.id} in guild '{guild_name}' "
            f"has fewer than 2 embeds, skipping info embed update"
        )
        return "error"

    new_embed = ChannelInfoEmbed(bot, channel, title, user_limit)
    if _info_embed_signature(control_message.embeds[1]) == _info_embed_signature(new_embed):
        return "skipped"

    embeds = list(control_message.embeds)
    embeds[1] = new_embed
    try:
        await control_message.edit(embeds=embeds)
    except discord.NotFound:
        logger.debug(
            f"Control message or channel gone for temp channel {channel.id} in guild '{guild_name}'"
        )
        if bot.repos.temp_channels.get_info(channel.id) is not None:
            bot.repos.temp_channels.remove(channel.id)
        return "not_found"
    except discord.HTTPException as error:
        if error.status == 429:
            retry_seconds = getattr(error, "retry_after", 10)
            logger.debug(
                f"Embed edit rate limited for temp channel {channel.id} in guild '{guild_name}', "
                f"retrying in {retry_seconds + 1}s"
            )
            await asyncio.sleep(retry_seconds + 1)
            return "rate_limited"
        logger.warning(
            f"Failed to update control message info embed for temp channel {channel.id} "
            f"in guild '{guild_name}': {error}"
        )
        return "error"
    except Exception as error:
        logger.warning(
            f"Failed to update control message info embed for temp channel {channel.id} "
            f"in guild '{guild_name}': {error}"
        )
        return "error"

    logger.debug(f"Updated control message info embed for temp channel {channel.id} in guild '{guild_name}'")
    return "edited"

