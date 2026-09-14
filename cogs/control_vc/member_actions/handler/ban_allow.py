import discord
from cogs.control_vc.enums import Action
from cogs.control_vc.member_actions.handler.actions import _valid_targets, logger

BAN_PERMS = {
    "connect": False,
    "view_channel": False,
}

ALLOW_PERMS = {
    "connect": True,
    "view_channel": True,
}


async def _apply_overwrites(channel, targets, perms):
    # set_permissions is one request per target
    # Discord rate-limits 10 every 10 seconds.
    # so bulk edit if more than 10.
    if len(targets) > 10:
        overwrites = channel.overwrites
        overwrite = discord.PermissionOverwrite(**perms)
        for target in targets:
            overwrites[target] = overwrite
        await channel.edit(overwrites=overwrites)
    else:
        for target in targets:
            await channel.set_permissions(target, **perms)

    return targets


async def _apply_access(bot, channel, action, targets):
    valid = _valid_targets(bot, channel, action, targets)
    perms = BAN_PERMS if action == Action.BAN else ALLOW_PERMS
    affected = await _apply_overwrites(channel, valid, perms)

    if action == Action.BAN:
        connected = set(channel.members)
        for target in affected:
            if isinstance(target, discord.Member) and target in connected:
                try:
                    await target.move_to(None)
                except discord.HTTPException as e:
                    logger.warning(
                        f"Failed to disconnect {target} from temp channel {channel.id} "
                        f"in guild '{channel.guild.name}': {e}"
                    )

    return affected
