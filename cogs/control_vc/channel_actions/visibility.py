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
    channel = interaction.channel
    if new_state == ChannelState.HIDDEN.value:
        state_name = "hidden"
        new_overwrite = discord.PermissionOverwrite(**HIDE_PERMS)
    elif new_state == ChannelState.LOCKED.value:
        state_name = "locked"
        new_overwrite = discord.PermissionOverwrite(**LOCK_PERMS)
    else:
        state_name = "public"
        new_overwrite = discord.PermissionOverwrite(**PUBLIC_PERMS)

    logger.debug(
        f"Setting temp channel {channel.id} to {state_name} in guild '{interaction.guild.name}'"
    )

    try:
        updated = await _update_overwrites(bot, channel, new_overwrite)
    except discord.Forbidden as e:
        logger.warning(
            f"Missing permission to change access for temp channel {channel.id} in guild '{interaction.guild.name}': {e}"
        )
        await _notify_missing_overwrite_permission(interaction)
        return

    if not updated:
        return

    bot.repos.temp_channels.change_state(channel.id, new_state)
