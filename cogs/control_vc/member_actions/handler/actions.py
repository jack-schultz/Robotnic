import logging
import discord
from cogs.control_vc.enums import Action
from cogs.control_vc.owner import claim_or_verify_owner

logger = logging.getLogger("cogs.control_vc.member_actions.handler")

_PUNITIVE = {Action.BAN, Action.MUTE, Action.DEAFEN}
_VOICE = {Action.MUTE, Action.UNMUTE, Action.DEAFEN, Action.UNDEAFEN}

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
    if interaction.response.is_done():
        reply = await interaction.followup.send(message, ephemeral=True, wait=True)
        await reply.delete(delay=15)
    else:
        await interaction.response.send_message(message, ephemeral=True, delete_after=15)


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


async def handle_action(bot, interaction, actions, targets, channel=None):
    from cogs.control_vc.member_actions.handler.ban_allow import _apply_access
    from cogs.control_vc.member_actions.handler.mute_deafen import (
        _apply_sanction,
        _sync_member_voice,
    )

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

    reply = await interaction.followup.send(
        embed=_result_embed(actions, _unique(affected)),
        ephemeral=True,
        wait=True,
    )
    await reply.delete(delay=10)


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
