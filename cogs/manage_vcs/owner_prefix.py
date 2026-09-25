import logging
import discord

logger = logging.getLogger(__name__)

NICK_MAX_LENGTH = 32


def _get_owner_prefix(bot, member):
    settings = bot.repos.guild_settings.get(member.guild.id)
    if settings is None:
        logger.debug(
            f"Skipping owner prefix for {member} in guild '{member.guild.name}': no guild settings."
        )
        return None

    owner_prefix = settings["owner_prefix"]
    if not owner_prefix:
        logger.debug(
            f"Skipping owner prefix for {member} in guild '{member.guild.name}': owner prefix not configured."
        )
        return None

    return owner_prefix


def _can_edit_nick(member):
    me = member.guild.me
    if me is None:
        return False

    if not me.guild_permissions.manage_nicknames:
        logger.warning(
            f"Missing `manage_nicknames` permission to edit nick for {member} in guild '{member.guild.name}'"
        )
        return False

    if member.id == member.guild.owner_id:
        logger.debug(
            f"Cannot edit nick for guild owner {member} in guild '{member.guild.name}'"
        )
        return False

    if member.top_role >= me.top_role:
        logger.warning(
            f"Cannot edit nick for {member} in guild '{member.guild.name}': "
            f"member's top role is equal to or higher than the bot's top role `{me.top_role.name}`"
        )
        return False

    return True


async def _set_nick(member, nick, reason):
    try:
        await member.edit(nick=nick, reason=reason)
        logger.debug(
            f"Set nick for {member} to `{nick}` in guild '{member.guild.name}' ({reason})"
        )
    except discord.Forbidden as e:
        logger.warning(
            f"Permission error editing nick for {member} in guild '{member.guild.name}'. {e}"
        )
    except discord.HTTPException as e:
        logger.debug(
            f"Could not edit nick for {member} in guild '{member.guild.name}'. {e}"
        )


async def give_owner_prefix(bot, member):
    if member is None:
        return

    owner_prefix = _get_owner_prefix(bot, member)
    if owner_prefix is None:
        return

    if not _can_edit_nick(member):
        return

    current_nick = member.nick
    if current_nick is not None and current_nick.startswith(owner_prefix):
        logger.debug(
            f"{member} already has owner prefix nick in guild '{member.guild.name}', skipping."
        )
        return

    base_name = current_nick if current_nick is not None else member.display_name
    new_nick = f"{owner_prefix}{base_name}"[:NICK_MAX_LENGTH]

    if new_nick == current_nick:
        return

    await _set_nick(member, new_nick, "Owner prefix assignment")


async def remove_owner_prefix(bot, member):
    if member is None:
        return

    # Keep the prefix if they still own another temp channel
    if member.id in bot.repos.temp_channels.get_owner_ids(member.guild.id):
        logger.debug(
            f"{member} still owns a temp channel in guild '{member.guild.name}', "
            f"keeping owner prefix."
        )
        return

    owner_prefix = _get_owner_prefix(bot, member)
    if owner_prefix is None:
        return

    if not _can_edit_nick(member):
        return

    current_nick = member.nick
    if current_nick is None or not current_nick.startswith(owner_prefix):
        return

    new_nick = current_nick[len(owner_prefix):] or None
    await _set_nick(member, new_nick, "Owner prefix removal")
