import discord
import logging
from cogs.control_vc.enums import ChannelState

logger = logging.getLogger(__name__)


PUBLIC_PERMS = {
    "connect": True,
    "view_channel": True,
}
LOCK_PERMS = {
    "connect": False,
    "view_channel": True,
}
HIDE_PERMS = {
    "connect": False,
    "view_channel": False,
}


async def _update_overwrites(bot, channel, new_overwrite):
    creator_id = bot.repos.temp_channels.get_info(channel.id).creator_id
    default_role_id = bot.repos.creator_channels.get_info(creator_id).default_role_id
    if default_role_id is None:
        default_role = channel.guild.default_role
    else:
        default_role = channel.guild.get_role(default_role_id)

    overwrites = channel.overwrites
    overwrites[default_role] = new_overwrite
    await channel.edit(overwrites=overwrites)


async def channel_action(bot, interaction, new_state):
    # Hidden
    if new_state == ChannelState.HIDDEN.value:
        logger.debug(
            f"Setting temp channel {interaction.channel.id} to hidden in guild '{interaction.guild.name}'"
        )
        bot.repos.temp_channels.change_state(interaction.channel.id, ChannelState.HIDDEN.value)
        new_overwrite = discord.PermissionOverwrite(**HIDE_PERMS)
        await _update_overwrites(bot, interaction.channel, new_overwrite)

    # Locked
    elif new_state == ChannelState.LOCKED.value:
        logger.debug(
            f"Setting temp channel {interaction.channel.id} to locked in guild '{interaction.guild.name}'"
        )
        bot.repos.temp_channels.change_state(interaction.channel.id, ChannelState.LOCKED.value)
        new_overwrite = discord.PermissionOverwrite(**LOCK_PERMS)
        await _update_overwrites(bot, interaction.channel, new_overwrite)

    # Public
    else:
        logger.debug(
            f"Setting temp channel {interaction.channel.id} to public in guild '{interaction.guild.name}'"
        )
        bot.repos.temp_channels.change_state(interaction.channel.id, ChannelState.PUBLIC.value)
        new_overwrite = discord.PermissionOverwrite(**PUBLIC_PERMS)
        await _update_overwrites(bot, interaction.channel, new_overwrite)
