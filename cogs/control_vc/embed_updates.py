import asyncio
import logging
import discord
from cogs.control_vc.embeds import ChannelInfoEmbed

logger = logging.getLogger(__name__)


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
    async for message in channel.history(limit=1, oldest_first=True):
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
