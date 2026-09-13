import logging

import discord

from cogs.control_vc.enums import Action
from cogs.control_vc.owner import claim_or_verify_owner

logger = logging.getLogger(__name__)

BAN_PERMS = {
    "connect": False,
    "view_channel": False,
}

ALLOW_PERMS = {
    "connect": True,
    "view_channel": True,
}

_PUNITIVE = {Action.BAN, Action.MUTE, Action.DEAFEN}
_VOICE = {Action.MUTE, Action.UNMUTE, Action.DEAFEN, Action.UNDEAFEN}
_FLAG = {
    Action.MUTE: ("muted", True),
    Action.UNMUTE: ("muted", False),
    Action.DEAFEN: ("deafened", True),
    Action.UNDEAFEN: ("deafened", False),
}

_RESPONSES = {
    Action.BAN: {
        "title": "Banned!",
        "one": "Banned {mention} from your channel.",
        "many": "Banned {count} member(s)/role(s) from your channel.",
        "none": "No bannable users or roles were selected.",
    },
    Action.ALLOW: {
        "title": "Allowed!",
        "one": "Allowed {mention} to your channel.",
        "many": "Allowed {count} member(s)/role(s) in your channel.",
        "none": "No allowable users or roles were selected.",
    },
    Action.MUTE: {
        "title": "Muted!",
        "one": "Muted {mention} in your channel.",
        "many": "Muted {count} member(s) in your channel.",
        "none": "No mutable members were selected.",
    },
    Action.UNMUTE: {
        "title": "Unmuted!",
        "one": "Unmuted {mention} in your channel.",
        "many": "Unmuted {count} member(s) in your channel.",
        "none": "No unmuteable members were selected.",
    },
    Action.DEAFEN: {
        "title": "Deafened!",
        "one": "Deafened {mention} in your channel.",
        "many": "Deafened {count} member(s) in your channel.",
        "none": "No deafenable members were selected.",
    },
    Action.UNDEAFEN: {
        "title": "Undeafened!",
        "one": "Undeafened {mention} in your channel.",
        "many": "Undeafened {count} member(s) in your channel.",
        "none": "No undeafenable members were selected.",
    },
}

# Members whose next same-channel mute/deafen event was caused by this process.
_pending_edits = set()


_UNMUTE_AND_UNDEAFEN = {
    "title": "Unmuted and undeafened!",
    "one": "Unmuted and undeafened {mention}.",
    "many": "Unmuted and undeafened {count} member(s).",
    "none": "No members could be unmuted and undeafened.",
}


def _unique(items):
    seen = set()
    unique = []
    for item in items:
        if item.id in seen:
            continue
        seen.add(item.id)
        unique.append(item)
    return unique


async def _reply_error(interaction, message):
    kwargs = {"ephemeral": True, "delete_after": 15}
    if interaction.response.is_done():
        await interaction.followup.send(message, **kwargs)
    else:
        await interaction.response.send_message(message, **kwargs)


async def _resolve_channel(bot, user):
    if not isinstance(user, discord.Member) or user.voice is None or user.voice.channel is None:
        return None, f"You are not connected to a voice channel {user.mention}!"

    channel = user.voice.channel
    if bot.repos.temp_channels.get_info(channel.id) is None:
        return None, "This is not a controlled voice channel."
    return channel, None


def _valid_targets(bot, channel, action, targets):
    info = bot.repos.temp_channels.get_info(channel.id)
    owner_id = info.owner_id if info else None
    valid = []

    for target in targets:
        if not target:
            continue
        if action in _VOICE:
            if not isinstance(target, discord.Member) or target.id == bot.user.id:
                continue
        if action in _PUNITIVE and isinstance(target, discord.Member):
            if target.id == owner_id or target.id == bot.user.id:
                continue
        valid.append(target)

    return valid


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


def take_pending_edit(member):
    key = (member.guild.id, member.id)
    if key not in _pending_edits:
        return False
    _pending_edits.discard(key)
    return True


async def note_external_server_mute(bot, member, after):
    if member.bot or take_pending_edit(member):
        return
    bot.repos.voice_sanctions.update_prior(member.guild.id, member.id, after.mute, after.deaf)


async def _edit_voice(member, muted, deafened):
    target_mute = bool(deafened)
    target_deaf = bool(deafened)
    key = (member.guild.id, member.id)
    _pending_edits.add(key)
    try:
        await member.edit(mute=target_mute, deafen=target_deaf)
    except discord.Forbidden as e:
        _pending_edits.discard(key)
        logger.warning(
            f"Missing permission to set mute={target_mute} deafen={target_deaf} for {member} "
            f"in guild '{member.guild.name}': {e}"
        )
        return False
    except discord.HTTPException as e:
        _pending_edits.discard(key)
        logger.debug(
            f"Could not set mute={target_mute} deafen={target_deaf} for {member} "
            f"in guild '{member.guild.name}': {e}"
        )
        return False
    return True


def _already_applied(member, muted, deafened):
    voice = member.voice
    if voice is None:
        return False
    return bool(voice.mute) == bool(muted or deafened) and bool(voice.deaf) == bool(deafened)


async def _apply_bot_voice(bot, member, muted, deafened):
    if member.voice is None or member.voice.channel is None:
        return False
    if _already_applied(member, muted, deafened):
        return True
    bot.repos.voice_sanctions.save_prior(
        member.guild.id, member.id, member.voice.mute, member.voice.deaf
    )
    return await _edit_voice(member, muted, deafened)


async def _restore_prior(bot, member):
    prior = bot.repos.voice_sanctions.get_prior(member.guild.id, member.id)
    if prior is None:
        return False
    if member.voice is None or member.voice.channel is None:
        return False
    muted, deafened = prior
    if _already_applied(member, muted, deafened):
        bot.repos.voice_sanctions.clear_discord_reset(member.guild.id, member.id)
        return True
    if await _edit_voice(member, muted, deafened):
        bot.repos.voice_sanctions.clear_discord_reset(member.guild.id, member.id)
        return True
    return False


def _in_channel(member, channel):
    voice = member.voice
    return voice is not None and voice.channel is not None and voice.channel.id == channel.id


async def _sync_member_voice(bot, channel, member):
    if not _in_channel(member, channel):
        return
    flags = bot.repos.voice_sanctions.get(channel.guild.id, channel.id, member.id)
    muted = flags[0] if flags else False
    deafened = flags[1] if flags else False
    await _apply_bot_voice(bot, member, muted, deafened)


async def _apply_sanction(bot, channel, action, targets):
    valid = _valid_targets(bot, channel, action, targets)
    field, value = _FLAG[action]
    for target in valid:
        bot.repos.voice_sanctions.set_flags(
            guild_id=channel.guild.id,
            channel_id=channel.id,
            user_id=target.id,
            **{field: value},
        )
    return valid


async def handle_action(bot, interaction, actions, targets, channel=None):
    if isinstance(actions, Action):
        actions = (actions,)
    actions = tuple(actions)

    user = interaction.user

    if channel is None:
        channel, error = await _resolve_channel(bot, user)
        if error:
            await _reply_error(interaction, error)
            return

    if bot.repos.temp_channels.get_info(channel.id) is None:
        await _reply_error(interaction, "This is not a controlled voice channel.")
        return

    ok, error = await claim_or_verify_owner(bot, channel, user)
    if not ok:
        await _reply_error(interaction, error)
        return

    if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=True)

    affected = []
    voice_touched = []
    for action in actions:
        if action in _VOICE:
            applied = await _apply_sanction(bot, channel, action, targets)
            voice_touched.extend(applied)
        else:
            applied = await _apply_access(bot, channel, action, targets)
        affected.extend(applied)

    for member in _unique(voice_touched):
        await _sync_member_voice(bot, channel, member)

    await interaction.followup.send(
        embed=_result_embed(actions, _unique(affected)),
        ephemeral=True,
        delete_after=10,
    )


def _result_embed(actions, affected):
    if set(actions) == {Action.UNMUTE, Action.UNDEAFEN}:
        copy = _UNMUTE_AND_UNDEAFEN
    else:
        copy = _RESPONSES[actions[0]]

    if len(affected) == 1:
        title = copy["title"]
        description = copy["one"].format(mention=affected[0].mention)
    elif len(affected) > 1:
        title = copy["title"]
        description = copy["many"].format(count=len(affected))
    else:
        title = copy["none"]
        description = ""

    embed = discord.Embed(title=title, description=description, color=0x00FF00)
    embed.set_footer(text="This message will disappear in 10 seconds.")
    return embed


async def clear_orphaned_sanctions(bot):
    deleted, affected = bot.repos.voice_sanctions.delete_invalid()
    if not deleted:
        return

    logger.debug(f"Removed {deleted} orphaned voice sanction row(s)")
    for guild_id, user_id in affected:
        guild = bot.get_guild(guild_id)
        member = guild.get_member(user_id) if guild else None
        if member is None:
            continue
        voice = member.voice
        channel = voice.channel if voice else None
        if channel is not None and bot.repos.temp_channels.get_info(channel.id) is not None:
            flags = bot.repos.voice_sanctions.get(guild_id, channel.id, user_id)
            if flags and (flags[0] or flags[1]):
                continue
        await _restore_prior(bot, member)


async def sync_sanctions_for_voice_state(bot, member, before, after):
    if member.bot:
        return

    before_channel = before.channel if before else None
    after_channel = after.channel if after else None
    if before_channel == after_channel:
        return

    if after_channel is not None:
        await _apply_or_clear_on_join(bot, member, after_channel)
    elif before_channel is not None:
        await _restore_prior(bot, member)


async def _apply_or_clear_on_join(bot, member, channel):
    removed_active = bot.repos.voice_sanctions.delete_invalid_for_user(channel.guild.id, member.id)
    if removed_active:
        logger.debug(
            f"Removed orphaned voice sanctions for {member} in guild '{channel.guild.name}'"
        )

    flags = None
    if bot.repos.temp_channels.get_info(channel.id) is not None:
        flags = bot.repos.voice_sanctions.get(channel.guild.id, channel.id, member.id)

    if flags and (flags[0] or flags[1]):
        await _apply_bot_voice(bot, member, flags[0], flags[1])
        return

    await _restore_prior(bot, member)
