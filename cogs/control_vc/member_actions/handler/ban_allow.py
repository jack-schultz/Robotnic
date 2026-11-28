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
ACCESS_PERMS = {
    Action.BAN: BAN_PERMS,
    Action.ALLOW: ALLOW_PERMS,
    Action.ENABLE_VOICE_ACTIVITY: {"use_voice_activation": True},
    Action.DISABLE_VOICE_ACTIVITY: {"use_voice_activation": False},
}


async def _apply_overwrites(channel, targets, perms):
    # set_permissions is one request per target
    # Discord rate-limits 10 every 10 seconds.
    # so bulk edit if more than 10.
    try:
        if len(targets) > 10:
            overwrites = channel.overwrites
            for target in targets:
                overwrite = channel.overwrites_for(target)
                overwrite.update(**perms)
                overwrites[target] = overwrite
            await channel.edit(overwrites=overwrites)
        else:
            for target in targets:
                overwrite = channel.overwrites_for(target)
                overwrite.update(**perms)
                await channel.set_permissions(target, overwrite=overwrite)
    except discord.Forbidden as e:
        logger.warning(
            f"Missing permission to edit overwrites for temp channel {channel.id} in guild '{channel.guild.name}': {e}"
        )
        return None

    return targets


async def _apply_access(bot, channel, action, targets):
    valid = _valid_targets(bot, channel, action, targets)
    affected = await _apply_overwrites(channel, valid, ACCESS_PERMS[action])
    if affected is None:
        return None

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
