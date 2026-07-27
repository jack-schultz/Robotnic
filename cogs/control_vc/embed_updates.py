import logging
from cogs.control_vc.embeds import ChannelInfoEmbed

logger = logging.getLogger(__name__)


async def update_info_embed(bot, channel, title=None, user_limit=None):
    guild_name = channel.guild.name
    control_message = None
    async for message in channel.history(limit=1, oldest_first=True):
        control_message = message
    if control_message is None:
        logger.warning(f"Failed to find control message for temp channel {channel.id} in guild '{guild_name}'")
        return
    embeds = control_message.embeds
    embeds[1] = ChannelInfoEmbed(bot, channel, title, user_limit)
    try:
        await control_message.edit(embeds=embeds)
    except Exception as e:
        logger.warning(
            f"Failed to update control message info embed for temp channel {channel.id} in guild '{guild_name}': {e}"
        )
        return
    logger.debug(f"Updated control message info embed for temp channel {channel.id} in guild '{guild_name}'")
