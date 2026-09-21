import logging
import discord
from cogs.control_vc.views.control_view import ControlView
from cogs.manage_vcs.child_settings import (
    collate_temp_channel_overwrites,
    get_child_category,
    get_child_overwrites,
)
from cogs.manage_vcs.create_name import create_temp_channel_name
from cogs.manage_vcs.owner_role import give_owner_role
from cogs.manage_vcs.notifications import dm_user_on_create, send_temp_channel_create_logs

logger = logging.getLogger(__name__)


def _next_temp_channel_count(bot, creator_channel_id, temp_channel_id, guild_name):
    counts = bot.repos.temp_channels.get_counts(creator_channel_id)
    if len(counts) < 1:
        count = 1
    else:
        count = max(counts) + 1
    logger.debug(
        f"Assigned count {count} to temp channel {temp_channel_id} from creator channel {creator_channel_id} in guild '{guild_name}'"
    )
    return count


REQUIRED_PERMISSIONS = (
    "view_channel",
    "manage_channels",
    "manage_roles",
    "send_messages",
    "embed_links",
    "manage_messages",
    "read_message_history",
    "connect",
    "move_members",
)
REQUIRED_PERMISSIONS_DISPLAY = ", ".join(f"`{perm}`" for perm in REQUIRED_PERMISSIONS)
MAX_OVERWRITE_ISSUES = 10
EMBED_FIELD_LIMIT = 1024


def _overwrite_target_label(target):
    if isinstance(target, discord.Role):
        return target.name
    if isinstance(target, (discord.Member, discord.User)):
        return str(target)
    return str(getattr(target, "id", target))


def _truncate_field(value):
    if len(value) <= EMBED_FIELD_LIMIT:
        return value
    return value[:EMBED_FIELD_LIMIT - 3] + "..."


def _collect_create_permission_issues(me, category, overwrites):
    """Collate parent and guild-role gaps that would stop channel creation.

    Discord validates create overwrites against the bot's guild role, not
    category-effective permissions. A category grant is not enough to set
    that bit on the new channel.
    """
    parent_perms = category.permissions_for(me) if category else me.guild_permissions
    parent_label = f"category `{category.name}`" if category else "the server"
    issues = [
        f"Missing in {parent_label}: `{perm}`"
        for perm in REQUIRED_PERMISSIONS
        if not getattr(parent_perms, perm, False)
    ]

    if me.guild_permissions.administrator:
        return issues

    guild_perms = me.guild_permissions
    seen = set()
    overwrite_count = 0
    for target, overwrite in overwrites.items():
        label = _overwrite_target_label(target)
        allow, deny = overwrite.pair()
        for perms in (allow, deny):
            for perm_name, is_set in perms:
                if not is_set or getattr(guild_perms, perm_name, False):
                    continue
                line = f"Needed on the bot's server role: `{perm_name}` for `{label}`"
                if line in seen:
                    continue
                seen.add(line)
                issues.append(line)
                overwrite_count += 1
                if overwrite_count >= MAX_OVERWRITE_ISSUES:
                    return issues
    return issues


async def _notify_missing_permissions(
    member,
    creator_channel,
    category,
    guild_name,
    issues,
    discord_error=None,
):
    detail = "; ".join(issues) if issues else (
        f"Discord: {discord_error}" if discord_error else "No diagnostic details"
    )
    logger.warning(
        f"Cannot create temp channel for {member} in guild '{guild_name}'. {detail}"
    )

    embed = discord.Embed()
    embed.add_field(name="Required", value=REQUIRED_PERMISSIONS_DISPLAY)
    if issues:
        embed.add_field(
            name="Missing",
            value=_truncate_field("\n".join(f"- {issue}" for issue in issues)),
        )
    elif discord_error:
        embed.add_field(name="Discord error", value=_truncate_field(discord_error))

    if issues:
        response_text = f"Sorry {member.mention}, I require the following permissions."
        if category:
            response_text += (
                f" Make sure they are not overwritten by the category (In this case `{category.name}`)."
            )
    else:
        response_text = (
            f"Sorry {member.mention}, I do not have permission to create a channel "
            f"in the desired category"
        )
        response_text += f" (`{category.name}`)." if category else "."

    creator_perms = creator_channel.permissions_for(member.guild.me)
    if creator_perms.send_messages and creator_perms.embed_links:
        try:
            await creator_channel.send(response_text, embed=embed, delete_after=300)
            logger.debug(
                f"Notified {member} of create permission issues in guild '{guild_name}'"
            )
            return
        except discord.Forbidden as e:
            logger.warning(
                f"Could not notify {member} of missing permissions in creator channel "
                f"{creator_channel.id} in guild '{guild_name}'. {e}"
            )
        except Exception as e:
            logger.warning(
                f"Error notifying {member} of missing permissions in guild '{guild_name}'. {e}"
            )
            return

    try:
        await member.send(response_text, embed=embed)
        logger.debug(f"DM'd {member} about create permission issues in guild '{guild_name}'")
    except discord.Forbidden as e:
        logger.warning(
            f"Could not DM {member} about missing permissions in guild '{guild_name}'. {e}"
        )
    except Exception as e:
        logger.warning(
            f"Error DM'ing {member} about missing permissions in guild '{guild_name}'. {e}"
        )


async def _notify_unexpected_forbidden(
    member, creator_channel, category, overwrites, guild_name, discord_error
):
    issues = _collect_create_permission_issues(member.guild.me, category, overwrites)
    await _notify_missing_permissions(
        member,
        creator_channel,
        category,
        guild_name,
        issues,
        discord_error=None if issues else discord_error,
    )


async def _create_temp_voice_channel(creator_channel, category, overwrites, member, guild_name):
    try:
        new_temp_channel = await creator_channel.guild.create_voice_channel(
            name="⌛",
            category=category,
            overwrites=overwrites,
            position=creator_channel.position,
            bitrate=creator_channel.bitrate
        )
    except discord.Forbidden as e:
        discord_error = e.text or str(e)
        logger.warning(
            f"Permission error creating temp channel in guild '{guild_name}'. {discord_error}"
        )
        await _notify_unexpected_forbidden(
            member, creator_channel, category, overwrites, guild_name, discord_error
        )
        return None

    logger.debug(
        f"Created temp channel {new_temp_channel.id} for {member} in category "
        f"{category.name if category else 'none'} in guild '{guild_name}'"
    )
    return new_temp_channel


async def _move_member_to_temp_channel(member, temp_channel, guild_name):
    try:
        await member.move_to(temp_channel)
        logger.debug(f"Moved {member} to {temp_channel} in guild '{guild_name}'")
    except Exception as e:
        logger.debug(
            f"Error creating voice channel in guild '{guild_name}', most likely a quick join and leave. Handled. {e}"
        )
        await temp_channel.delete()
        return False
    return True


async def _finalize_temp_channel(
    bot,
    temp_channel,
    member,
    db_info,
    channel_name,
    guild_name,
    creator_channel,
    category,
    overwrites,
):
    try:
        # Could use bot.TempChannelRenamer to avoid rate-limit problems but this does not support user limit yet
        # Fine to use without scheduling as rate limit bucket will never be full immediately after creation
        await temp_channel.edit(
            name=channel_name,
            user_limit=db_info.user_limit,
        )
    except discord.Forbidden as e:
        discord_error = e.text or str(e)
        logger.warning(
            f"Permission error renaming temp channel {temp_channel.id} in guild '{guild_name}'. {discord_error}"
        )
        await _notify_unexpected_forbidden(
            member, creator_channel, category, overwrites, guild_name, discord_error
        )
        return None
    except Exception as e:
        logger.warning(
            f"Error renaming temp channel {temp_channel.id} in guild '{guild_name}', handled. {e}"
        )
        return None

    try:
        view = ControlView.for_channel(bot, temp_channel)
        await view.send_control_message(temp_channel, member, channel_name=channel_name)
        logger.debug(
            f"Finalized temp channel {temp_channel.id} as '{channel_name}' "
            f"with control message in guild '{guild_name}'"
        )
        return view
    except discord.Forbidden as e:
        discord_error = e.text or str(e)
        logger.warning(
            f"Permission error sending control message for temp channel {temp_channel.id} "
            f"in guild '{guild_name}'. {discord_error}"
        )
        await _notify_unexpected_forbidden(
            member, creator_channel, category, overwrites, guild_name, discord_error
        )
        return None
    except Exception as e:
        logger.warning(
            f"Error sending control message for temp channel {temp_channel.id} "
            f"in guild '{guild_name}', handled. {e}"
        )
        raise
        return None


async def create_on_join(member, before, after, bot):
    guild_name = member.guild.name
    creator_channel = after.channel
    logger.debug(f"{member} joined creator channel {creator_channel} in guild '{guild_name}'")

    # Logic flow:
    # 1. Retrieve child settings from db
    # 2. Get category & overwrites, both depend on settings
    # 3. Collate overwrites
    # 4. Check all permissions; notify and stop if anything is missing
    # 5. Create channel & move user
    # 6. Add channel to DB
    # 7. Rename and send control message (slow; user is already in the channel)
    # 8. Send DM to Owner
    # 9. Give Owner set guild Owner Role
    # 10. Send Logs

    #  ========== 1. Get settings from DB ==========
    # SETTINGS needed from db for naming scheme
    # Category:
    # 0 -> Creator channel category
    # id -> Specific category
    # Note: no way to make channel have no category if the creator has a category
    # Overwrites:
    # 0 -> no overwrites
    # 1 -> overwrites from creator
    # 2 -> overwrites from category
    # User Limit:
    # 0 -> unlimited
    # int -> that amount
    # Name Template:
    # {user} - replaced by users nickname or display name
    # {activity} - replaced by activities being played in the vc, duplicates filtered out, ordered by shortest to longest name
    # {count} - replaced by a number, starts at 1, increments per temp channel
    db_info = bot.repos.creator_channels.get_info(creator_channel.id)

    #  ========== 2. Get category & overwrites ==========
    category = get_child_category(db_info, creator_channel, bot, guild_name)
    overwrites = get_child_overwrites(db_info, creator_channel, category, guild_name)

    #  ========== 3. Collate overwrites ==========
    collate_temp_channel_overwrites(overwrites, bot.user, member)

    #  ========== 4. Check all permissions ==========
    issues = _collect_create_permission_issues(member.guild.me, category, overwrites)
    if issues:
        await _notify_missing_permissions(
            member, creator_channel, category, guild_name, issues
        )
        return

    #  ========== 5. Create channel & move user ==========
    new_temp_channel = await _create_temp_voice_channel(
        creator_channel, category, overwrites, member, guild_name
    )
    if new_temp_channel is None:
        return
    if not await _move_member_to_temp_channel(member, new_temp_channel, guild_name):
        return

    #  ========== 6. Add channel to DB ==========
    count = _next_temp_channel_count(bot, creator_channel.id, new_temp_channel.id, guild_name)
    bot.repos.temp_channels.add(new_temp_channel.guild.id, new_temp_channel.id, creator_channel.id, member.id, 0, count, False)
    logger.debug(f"Registered temp channel {new_temp_channel.id} in database for owner {member.id} in guild '{guild_name}'")

    #  ========== 7. Rename and send control message (slow; user is already in the channel) ==========
    channel_name = create_temp_channel_name(bot, new_temp_channel, db_creator_channel_info=db_info)
    logger.debug(f"Generated temp channel name '{channel_name}' for {new_temp_channel.id} in guild '{guild_name}'")
    control_view = await _finalize_temp_channel(
        bot,
        new_temp_channel,
        member,
        db_info,
        channel_name,
        guild_name,
        creator_channel,
        category,
        overwrites,
    )
    if control_view is None:
        return

    # 8. ======== Send DM to Owner ==========
    await dm_user_on_create(bot, new_temp_channel, member, control_view)

    # 9. ======== Give Owner set guild Owner Role =========
    await give_owner_role(bot, member)

    # 10. ======== Send Logs ==========
    await send_temp_channel_create_logs(bot, new_temp_channel, member, guild_name)
