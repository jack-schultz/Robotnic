"""
Mute, unmute, deafen, and undeafen for temp voice channels.

These are channel sanctions, different from permission overwrites. A voice_sanctions
row is the owner's wish for one member in one temp channel. handle_action writes that row,
then member.edit pushes it as Discord server mute / server
deafen. The sanction is stored even if the target is not in the channel,
and the next join applies it. It sticks across leave and rejoin of that channel,
and is deleted when the temp channel is.

The channel_id=0 row is not a sanction. prior_muted / prior_deafened is the
server mute and deafen from before the bot overrode them,
so a moderator mute is restored on leave. It is written once. If they rejoin already in the
sanctioned state, that voice is not the prior.
Saving it would restore the sanction after the next leave and leave them stuck. That case stores
unmuted and undeafened instead.

Discord drops deaf when mute is in the same request, so a deafen change is its own edit and it goes first.
Voice state is snapshotted before either call.
The event from the first edit updates member.voice and must
not cause a second, unintended mute or deafen.

Every bot edit also produces a voice_state_update, indistinguishable from a
moderator. _expected_voice records the final (mute, deaf) before editing.
Two fields stop that record from being wrong:

held
    True for the whole in-flight edit. The deafen edit fires a voice event
    whose state is not the final target. Without held, that intermediate
    looks like a moderator: it would be written into prior_*,
    or it would resync and fight the edit still in progress.
    While held, any mute or deafen event for that member is ours, whether or not it matches.

gen
    Incremented on every edit attempt. A leftover expected entry used to survive leave
    and rejoin, swallow the next voice event, and
    skip writing prior_*. Join and leave call clear_voice_memory, which drops the entry.
    The in-flight edit keeps its own gen and bails via _still_expected if that entry is gone or replaced,
    so it does not send the second request and does not release a stale record.
    gen is what distinguishes an edit still
    in flight from one a channel change already invalidated.

On a clean finish, _release_expected drops the entry if the
matching event already arrived (seen) or the member has left voice. Otherwise it clears held and leaves the entry,
so a late gateway event can still be recognized as ours.
A failed or superseded edit deletes the entry instead.

A Discord side effect that is not a moderator override is resynced once.
_mismatch_corrected remembers that attempt so a second mismatch does not loop.
A moderator who changes a flag this channel actually set is not fought this session;
the new state is written into prior_*.
The channel row stays, so the next join of this channel applies the sanction again. A
change to a flag the sanction did not set is a side effect and is resynced.

Same-channel mute/deafen events go to note_external_server_mute.
A channel change clears expected state first, then applies this channel's flags or
restores the prior. A full leave restores the prior and deletes the sentinel row if the edit sticks.
"""

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

# In-flight bot edit, keyed by (guild_id, user_id). See the module docstring.
# state is the final (mute, deaf); gen is which edit; held ignores intermediates.
_expected_voice = {}
_mismatch_corrected = set()
_voice_gen = 0


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


def _voice_key(member):
    return member.guild.id, member.id


def clear_voice_memory(member):
    key = _voice_key(member)
    _expected_voice.pop(key, None)
    _mismatch_corrected.discard(key)


def _take_expected(member, after):
    key = _voice_key(member)
    pending = _expected_voice.get(key)
    if pending is None:
        return None
    state = (bool(after.mute), bool(after.deaf))
    if state == pending["state"]:
        if pending["held"]:
            pending["seen"] = True
        else:
            _expected_voice.pop(key, None)
        return "ours"
    if pending["held"]:
        return "ours"
    # Side effect of our edit, not a moderator. Drop it so it cannot swallow the rejoin.
    _expected_voice.pop(key, None)
    return "mismatch"


def _channel_flags(bot, member, after):
    channel = after.channel
    if channel is None or bot.repos.temp_channels.get_info(channel.id) is None:
        return None
    return bot.repos.voice_sanctions.get(channel.guild.id, channel.id, member.id)


def _sanction_overridden(flags, after):
    """A moderator changed a flag this channel actually set, not an extra the sanction never asked for."""
    if not flags or not (flags[0] or flags[1]):
        return False
    if flags[0] and bool(after.mute) != bool(flags[0]):
        return True
    if flags[1] and bool(after.deaf) != bool(flags[1]):
        return True
    return False


async def note_external_server_mute(bot, member, after):
    if member.bot:
        return
    key = _voice_key(member)
    taken = _take_expected(member, after)
    flags = _channel_flags(bot, member, after)
    if taken == "ours":
        _mismatch_corrected.discard(key)
        return
    if taken == "mismatch" and not _sanction_overridden(flags, after):
        if key in _mismatch_corrected:
            return
        _mismatch_corrected.add(key)
        await _resync_member_voice(bot, member)
        return
    if flags and (bool(after.mute), bool(after.deaf)) == (bool(flags[0]), bool(flags[1])):
        _mismatch_corrected.discard(key)
        return
    if flags and (flags[0] or flags[1]) and not _sanction_overridden(flags, after):
        if key in _mismatch_corrected:
            return
        _mismatch_corrected.add(key)
        await _resync_member_voice(bot, member)
        return
    bot.repos.voice_sanctions.update_prior(member.guild.id, member.id, after.mute, after.deaf)


def _begin_expected(member, muted, deafened):
    global _voice_gen
    _voice_gen += 1
    key = _voice_key(member)
    _expected_voice[key] = {
        "state": (bool(muted), bool(deafened)),
        "gen": _voice_gen,
        "held": True,
    }
    return key, _voice_gen


def _still_expected(key, gen):
    pending = _expected_voice.get(key)
    return pending is not None and pending["gen"] == gen


def _release_expected(key, gen, member):
    pending = _expected_voice.get(key)
    if pending is None or pending["gen"] != gen:
        return
    voice = member.voice
    if pending.get("seen") or voice is None or voice.channel is None:
        _expected_voice.pop(key, None)
        return
    pending["held"] = False


async def _edit_voice_field(member, **fields):
    try:
        await member.edit(**fields)
    except discord.Forbidden as e:
        logger.warning(
            f"Missing permission to set {fields} for {member} in guild '{member.guild.name}': {e}"
        )
        return False
    except discord.HTTPException as e:
        logger.debug(
            f"Could not set {fields} for {member} in guild '{member.guild.name}': {e}"
        )
        return False
    return True


async def _edit_voice(member, muted, deafened):
    # Server mute and server deafen are independent. Discord drops `deaf` when
    # `mute` is in the same request, so a deafen change has to be its own edit.
    # Snapshot once: a gateway event during the first edit updates the cache and
    # must not trigger a second, unintended mute or deafen.
    target_mute = bool(muted)
    target_deaf = bool(deafened)
    voice = member.voice
    if voice is None:
        return False
    current_mute = bool(voice.mute)
    current_deaf = bool(voice.deaf)
    key, gen = _begin_expected(member, target_mute, target_deaf)
    ok = False
    try:
        if current_deaf != target_deaf:
            if not await _edit_voice_field(member, deafen=target_deaf):
                return False
            if not _still_expected(key, gen):
                return False
        if current_mute != target_mute:
            if not await _edit_voice_field(member, mute=target_mute):
                return False
        ok = _still_expected(key, gen)
        return ok
    finally:
        if ok:
            _release_expected(key, gen, member)
        elif _still_expected(key, gen):
            _expected_voice.pop(key, None)


def _already_applied(member, muted, deafened):
    voice = member.voice
    if voice is None:
        return False
    return bool(voice.mute) == bool(muted) and bool(voice.deaf) == bool(deafened)


def _remember_prior(bot, member, muted, deafened):
    if bot.repos.voice_sanctions.has_stored_prior(member.guild.id, member.id):
        return
    voice = member.voice
    if voice is None:
        return
    # Already in the sanctioned state on rejoin. That voice is not the prior,
    # and leaving priors null is what leaves them stuck after the next leave.
    if _already_applied(member, muted, deafened):
        bot.repos.voice_sanctions.save_prior(member.guild.id, member.id, False, False)
        return
    bot.repos.voice_sanctions.save_prior(
        member.guild.id, member.id, voice.mute, voice.deaf
    )


async def _apply_bot_voice(bot, member, muted, deafened, remember_prior=True):
    if member.voice is None or member.voice.channel is None:
        return False
    if remember_prior:
        _remember_prior(bot, member, muted, deafened)
    if _already_applied(member, muted, deafened):
        return True
    return await _edit_voice(member, muted, deafened)


async def _resync_member_voice(bot, member):
    voice = member.voice
    channel = voice.channel if voice else None
    if channel is None:
        return
    if bot.repos.temp_channels.get_info(channel.id) is not None:
        flags = bot.repos.voice_sanctions.get(channel.guild.id, channel.id, member.id)
        if flags and (flags[0] or flags[1]):
            await _apply_bot_voice(bot, member, flags[0], flags[1], remember_prior=False)
            return
    await _restore_prior(bot, member)


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

    # A pending edit from the previous connection must not swallow this join.
    clear_voice_memory(member)

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
