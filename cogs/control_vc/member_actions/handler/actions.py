import logging
import discord
from cogs.control_vc.enums import Action
from cogs.control_vc.owner import claim_or_verify_owner
from config.i18n import t

logger = logging.getLogger("cogs.control_vc.member_actions.handler")


# Cant apply to self, bot or moderators
_PUNITIVE = {Action.BAN, Action.MUTE, Action.DEAFEN}
_VOICE = {Action.MUTE, Action.UNMUTE, Action.DEAFEN, Action.UNDEAFEN}
_MODERATOR_PERMS = [
    "manage_messages",
    "manage_channels",
    "administrator"
]

# Locale key prefixes for result messages, each has .title, .one, .many and .none
_RESPONSES = {
    Action.BAN: "actions.ban",
    Action.ALLOW: "actions.allow",
    Action.MUTE: "actions.mute",
    Action.UNMUTE: "actions.unmute",
    Action.DEAFEN: "actions.deafen",
    Action.UNDEAFEN: "actions.undeafen",
}

_UNMUTE_AND_UNDEAFEN = "actions.unmute_undeafen"


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


async def _resolve_channel(bot, user, lang):
    if not isinstance(user, discord.Member) or user.voice is None or user.voice.channel is None:
        return None, t("control.not_in_voice", lang, mention=user.mention)

    channel = user.voice.channel
    if bot.repos.temp_channels.get_info(channel.id) is None:
        return None, t("control.not_controlled", lang)
    return channel, None


def _valid_targets(bot, channel, action, targets):
    info = bot.repos.temp_channels.get_info(channel.id)
    owner_id = info.owner_id if info else None
    valid_targets = []

    for target in targets:
        # not None
        if not target:
            continue
        # Not a role if voice action
        if action in _VOICE:
            if not isinstance(target, discord.Member) or target.id == bot.user.id:
                continue
        # Prevent punitive action to self or bot or member moderators
        if action in _PUNITIVE and isinstance(target, discord.Member):
            if target.id == owner_id or target.id == bot.user.id:
                continue

            target_permissions = channel.permissions_for(target)
            is_moderator = any(getattr(target_permissions, perm, False) for perm in _MODERATOR_PERMS)
            if is_moderator:
                continue

        # Prevent punitive action to moderator roles
        if action in _PUNITIVE and isinstance(target, discord.Role):
            target_permissions = channel.permissions_for(target)
            is_moderator = any(getattr(target_permissions, perm, False) for perm in _MODERATOR_PERMS)
            if is_moderator:
                continue

        valid_targets.append(target)

    return valid_targets


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
    lang = bot.repos.guild_settings.get_language(interaction.guild_id)

    if channel is None:
        channel, error = await _resolve_channel(bot, user, lang)
        if error:
            await _reply_error(interaction, error)
            return

    if bot.repos.temp_channels.get_info(channel.id) is None:
        await _reply_error(interaction, t("control.not_controlled", lang))
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
            if applied is None:
                await _reply_error(
                    interaction,
                    t("common.no_permission_access", lang, mention=user.mention),
                )
                return
        affected.extend(applied)

    for member in _unique(voice_touched):
        await _sync_member_voice(bot, channel, member)

    reply = await interaction.followup.send(
        embed=_result_embed(actions, _unique(affected), lang),
        ephemeral=True,
        wait=True,
    )
    await reply.delete(delay=10)


def _result_embed(actions, affected, lang):
    if set(actions) == {Action.UNMUTE, Action.UNDEAFEN}:
        prefix = _UNMUTE_AND_UNDEAFEN
    else:
        prefix = _RESPONSES[actions[0]]

    if len(affected) == 1:
        title = t(f"{prefix}.title", lang)
        description = t(f"{prefix}.one", lang, mention=affected[0].mention)
    elif len(affected) > 1:
        title = t(f"{prefix}.title", lang)
        description = t(f"{prefix}.many", lang, count=len(affected))
    else:
        title = t(f"{prefix}.none", lang)
        description = ""

    embed = discord.Embed(title=title, description=description, color=0x00FF00)
    embed.set_footer(text=t("common.disappear_seconds", lang, seconds=10))
    return embed
