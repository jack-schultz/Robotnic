import logging
import discord
from cogs.control_vc.views.control_view import ControlView
from cogs.manage_vcs.child_settings import (
    collate_temp_channel_overwrites,
    get_child_category,
    get_child_overwrites,
)
from cogs.manage_vcs.create_name import create_temp_channel_name
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


PERMISSIONS_TO_CHECK = [
    "manage_channels",
    "manage_roles",
    "view_channel",
    "send_messages",
    "connect",
    "move_members",
    "manage_messages",
    "read_message_history",
]
REQUIRED_PERMISSIONS_DISPLAY = (
    "`view_channel`, `manage_channels`, `manage_roles`, `send_messages`, "
    "`manage_messages`, `read_message_history`, `connect`, `move_members`"
)
MAX_OVERWRITE_ISSUES = 10


def _missing_permissions_from(permissions):
    return [
        perm
        for perm in PERMISSIONS_TO_CHECK
        if not getattr(permissions, perm, False)
    ]


def _overwrite_target_label(target):
    if isinstance(target, discord.Role):
        return target.name
    if isinstance(target, (discord.Member, discord.User)):
        return str(target)
    return str(getattr(target, "id", target))


def _has_explicit_manage_roles_overwrite(me, category):
    if not category:
        return False
    member_overwrite = category.overwrites_for(me)
    if member_overwrite.manage_roles is True:
        return True
    for role in me.roles:
        role_overwrite = category.overwrites_for(role)
        if role_overwrite.manage_roles is True:
            return True
    return False


def _overwrite_permission_names(overwrite):
    names = []
    allow, deny = overwrite.pair()
    for perms, action in ((allow, "allow"), (deny, "deny")):
        for perm_name, is_set in perms:
            if is_set:
                names.append(f"{action}:{perm_name}")
    return names


def _diagnose_create_overwrites(me, category, overwrites):
    """Discord validates create overwrites against guild permissions, not category-effective ones."""
    if me.guild_permissions.administrator:
        return []

    guild_perms = me.guild_permissions
    can_set_manage_roles = _has_explicit_manage_roles_overwrite(me, category)
    issues = []

    for target, overwrite in overwrites.items():
        label = _overwrite_target_label(target)
        allow, deny = overwrite.pair()
        for perms in (allow, deny):
            for perm_name, is_set in perms:
                if not is_set:
                    continue
                if perm_name == "manage_roles":
                    if not can_set_manage_roles:
                        issues.append(
                            f"`manage_roles` for `{label}` "
                            f"(needs Administrator or a category overwrite granting me `manage_roles`)"
                        )
                elif not getattr(guild_perms, perm_name, False):
                    issues.append(
                        f"`{perm_name}` for `{label}` (bot lacks this on its guild role)"
                    )
                if len(issues) >= MAX_OVERWRITE_ISSUES:
                    return issues
    return issues


def _format_overwrite_dump(me, category, overwrites):
    """Build a log-friendly dump when Discord rejects create but diagnosis is empty."""
    guild_perms = me.guild_permissions
    category_perms = category.permissions_for(me) if category else None
    lines = [
        f"bot guild administrator={guild_perms.administrator}",
        f"bot has explicit category manage_roles overwrite="
        f"{_has_explicit_manage_roles_overwrite(me, category)}",
    ]
    for target, overwrite in overwrites.items():
        label = _overwrite_target_label(target)
        bits = _overwrite_permission_names(overwrite)
        missing_on_guild = []
        allow, deny = overwrite.pair()
        for perms in (allow, deny):
            for perm_name, is_set in perms:
                if not is_set:
                    continue
                if perm_name == "manage_roles":
                    if not guild_perms.administrator and not _has_explicit_manage_roles_overwrite(
                        me, category
                    ):
                        missing_on_guild.append(perm_name)
                elif not getattr(guild_perms, perm_name, False):
                    missing_on_guild.append(perm_name)
        line = f"overwrite `{label}`: {', '.join(bits) if bits else '(empty)'}"
        if missing_on_guild:
            line += f" | missing on guild role: {', '.join(sorted(set(missing_on_guild)))}"
        if category_perms is not None:
            missing_on_category = []
            for perms in (allow, deny):
                for perm_name, is_set in perms:
                    if is_set and perm_name != "manage_roles" and not getattr(
                        category_perms, perm_name, False
                    ):
                        missing_on_category.append(perm_name)
            if missing_on_category:
                line += (
                    f" | missing on category: {', '.join(sorted(set(missing_on_category)))}"
                )
        lines.append(line)
    return lines


async def _send_missing_permissions_notice(
    member,
    creator_channel,
    category,
    guild_name,
    scope_label,
    missing_permissions=None,
    overwrite_issues=None,
    discord_error=None,
):
    missing_permissions = missing_permissions or []
    overwrite_issues = overwrite_issues or []
    detail_parts = []
    if missing_permissions:
        detail_parts.append(f"Missing: {', '.join(missing_permissions)}")
    if overwrite_issues:
        detail_parts.append(f"Overwrite issues: {', '.join(overwrite_issues)}")
    if discord_error:
        detail_parts.append(f"Discord: {discord_error}")
    logger.warning(
        f"Cannot create temp channel for {member} in guild '{guild_name}' ({scope_label}). "
        + ("; ".join(detail_parts) if detail_parts else "No diagnostic details")
    )
    logger.debug(f"Notified {member} of create permission issues in guild '{guild_name}'")

    embed = discord.Embed()
    embed.add_field(name="Required", value=REQUIRED_PERMISSIONS_DISPLAY)
    if missing_permissions:
        embed.add_field(
            name="Missing",
            value=f"{', '.join(f'`{perm}`' for perm in missing_permissions)}",
        )
    if overwrite_issues:
        issues_value = "\n".join(f"- {issue}" for issue in overwrite_issues)
        if len(issues_value) > 1024:
            issues_value = issues_value[:1021] + "..."
        embed.add_field(name="Overwrite issues", value=issues_value)
    if discord_error and not missing_permissions and not overwrite_issues:
        error_value = discord_error if len(discord_error) <= 1024 else discord_error[:1021] + "..."
        embed.add_field(name="Discord error", value=error_value)

    if missing_permissions:
        response_text = f"Sorry {member.mention}, I require the following permissions."
        if category:
            response_text = (
                response_text
                + f" Make sure they are not overwritten by the category (In this case `{category.name}`)."
            )
    elif overwrite_issues:
        response_text = (
            f"Sorry {member.mention}, I cannot apply the configured permission overwrites "
            f"when creating the channel."
        )
        if category:
            response_text = (
                response_text
                + f" Make sure they are not overwritten by the category (In this case `{category.name}`)."
            )
    else:
        response_text = (
            f"Sorry {member.mention}, I do not have permission to create a channel "
            f"in the desired category"
        )
        if category:
            response_text = response_text + f" (`{category.name}`)."
        else:
            response_text = response_text + "."
    try:
        await creator_channel.send(response_text, embed=embed, delete_after=300)
    except discord.Forbidden as e:
        logger.warning(
            f"Could not notify {member} of missing permissions in creator channel {creator_channel.id} in guild '{guild_name}'. {e}"
        )
    except Exception as e:
        logger.warning(
            f"Error notifying {member} of missing permissions in guild '{guild_name}'. {e}"
        )


async def _notify_if_missing_guild_permissions(member, creator_channel, category, guild_name):
    missing_permissions = _missing_permissions_from(member.guild.me.guild_permissions)
    if missing_permissions:
        await _send_missing_permissions_notice(
            member,
            creator_channel,
            category,
            guild_name,
            "guild",
            missing_permissions=missing_permissions,
        )
        return False
    return True


async def _notify_if_missing_category_permissions(member, creator_channel, category, guild_name):
    if not category:
        return True
    missing_permissions = _missing_permissions_from(
        category.permissions_for(member.guild.me)
    )
    if missing_permissions:
        await _send_missing_permissions_notice(
            member,
            creator_channel,
            category,
            guild_name,
            "category",
            missing_permissions=missing_permissions,
        )
        return False
    return True


async def _notify_if_invalid_create_overwrites(
    member, creator_channel, category, overwrites, guild_name
):
    me = member.guild.me
    overwrite_issues = _diagnose_create_overwrites(me, category, overwrites)
    if overwrite_issues:
        await _send_missing_permissions_notice(
            member,
            creator_channel,
            category,
            guild_name,
            "overwrites",
            overwrite_issues=overwrite_issues,
        )
        return False
    return True


async def _create_temp_voice_channel(creator_channel, category, overwrites, member, guild_name):
    try:
        new_temp_channel = await creator_channel.guild.create_voice_channel(
            name="⌛",
            category=category,
            overwrites=overwrites,
            position=creator_channel.position,
        )
    except discord.Forbidden as e:
        me = member.guild.me
        missing_permissions = []
        if category:
            missing_permissions = _missing_permissions_from(category.permissions_for(me))
        overwrite_issues = _diagnose_create_overwrites(me, category, overwrites)
        discord_error = e.text or str(e)
        logger.warning(
            f"Permission error creating temp channel in category in guild '{guild_name}'. {e}"
        )
        if overwrite_issues:
            logger.warning(
                f"Overwrite diagnosis for guild '{guild_name}': {', '.join(overwrite_issues)}"
            )
        else:
            for line in _format_overwrite_dump(me, category, overwrites):
                logger.warning(f"Create Forbidden dump ({guild_name}): {line}")
        await _send_missing_permissions_notice(
            member,
            creator_channel,
            category,
            guild_name,
            "category",
            missing_permissions=missing_permissions,
            overwrite_issues=overwrite_issues,
            discord_error=discord_error,
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


FINALIZE_EDIT_PERMISSIONS = ["manage_channels"]
FINALIZE_SEND_PERMISSIONS = [
    "view_channel",
    "send_messages",
    "embed_links",
    "read_message_history",
]


def _missing_channel_permissions(channel, me, required_permissions):
    perms = channel.permissions_for(me)
    return [
        perm
        for perm in required_permissions
        if not getattr(perms, perm, False)
    ]


async def _notify_finalize_permission_failure(
    member,
    creator_channel,
    temp_channel,
    guild_name,
    action,
    missing_permissions,
    discord_error,
):
    detail = (
        f"Missing in `{temp_channel}`: {', '.join(missing_permissions)}"
        if missing_permissions
        else f"Discord: {discord_error}"
    )
    logger.warning(
        f"Cannot {action} for temp channel {temp_channel.id} in guild '{guild_name}'. {detail}"
    )

    response_text = (
        f"Sorry {member.mention}, I could not {action} in {temp_channel.mention}."
    )
    embed = discord.Embed()
    embed.add_field(
        name="Required",
        value=", ".join(f"`{perm}`" for perm in (
            FINALIZE_EDIT_PERMISSIONS if action == "rename the channel"
            else FINALIZE_SEND_PERMISSIONS
        )),
    )
    if missing_permissions:
        embed.add_field(
            name="Missing in temp channel",
            value=", ".join(f"`{perm}`" for perm in missing_permissions),
        )
    else:
        error_value = discord_error if len(discord_error) <= 1024 else discord_error[:1021] + "..."
        embed.add_field(name="Discord error", value=error_value)

    for notify_channel in (temp_channel, creator_channel):
        try:
            await notify_channel.send(response_text, embed=embed, delete_after=300)
            return
        except discord.Forbidden:
            try:
                await notify_channel.send(
                    f"{response_text} Missing: "
                    f"{', '.join(f'`{perm}`' for perm in missing_permissions) if missing_permissions else discord_error}",
                    delete_after=300,
                )
                return
            except Exception:
                continue
        except Exception as e:
            logger.warning(
                f"Error notifying {member} about finalize failure in guild '{guild_name}'. {e}"
            )
    logger.warning(
        f"Could not notify {member} of finalize failure for temp channel {temp_channel.id} "
        f"in guild '{guild_name}'"
    )


async def _finalize_temp_channel(
    bot, temp_channel, member, db_info, channel_name, guild_name, creator_channel
):
    me = temp_channel.guild.me
    try:
        # Could use bot.TempChannelRenamer to avoid rate-limit problems but this does not support user limit yet
        # Fine to use without scheduling as rate limit bucket will never be full immediately after creation
        await temp_channel.edit(
            name=channel_name,
            user_limit=db_info.user_limit,
        )
    except discord.Forbidden as e:
        missing = _missing_channel_permissions(temp_channel, me, FINALIZE_EDIT_PERMISSIONS)
        await _notify_finalize_permission_failure(
            member,
            creator_channel,
            temp_channel,
            guild_name,
            "rename the channel",
            missing,
            e.text or str(e),
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
        missing = _missing_channel_permissions(temp_channel, me, FINALIZE_SEND_PERMISSIONS)
        if not missing:
            # Effective perms look fine; dump channel overwrites for support logs.
            for target, overwrite in temp_channel.overwrites.items():
                bits = _overwrite_permission_names(overwrite)
                logger.warning(
                    f"Control message Forbidden dump ({guild_name}): "
                    f"`{_overwrite_target_label(target)}` -> {', '.join(bits) if bits else '(empty)'}"
                )
            perms = temp_channel.permissions_for(me)
            logger.warning(
                f"Control message Forbidden dump ({guild_name}): bot effective in channel: "
                + ", ".join(
                    f"{perm}={getattr(perms, perm, False)}"
                    for perm in FINALIZE_SEND_PERMISSIONS
                )
            )
        await _notify_finalize_permission_failure(
            member,
            creator_channel,
            temp_channel,
            guild_name,
            "send the control message",
            missing,
            e.text or str(e),
        )
        return None
    except Exception as e:
        logger.warning(
            f"Error sending control message for temp channel {temp_channel.id} "
            f"in guild '{guild_name}', handled. {e}"
        )
        return None


async def create_on_join(member, before, after, bot):
    guild_name = member.guild.name
    creator_channel = after.channel
    logger.debug(f"{member} joined creator channel {creator_channel} in guild '{guild_name}'")

    # Logic flow:
    # 1. Retrieve child settings from db
    # 2. Get category & overwrites, both depend on settings
    # 3. Notify of missing permissions
    # 4. Collate overwrites
    # 5. Create channel & move user
    # 6. Add channel to DB
    # 7. Update channel named based on naming scheme, this is slow and is therefore done last
    # 8. Send DM to Owner
    # 9. Send Logs

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

    #  ========== 3. Notify of missing permissions ==========
    if not await _notify_if_missing_guild_permissions(member, creator_channel, category, guild_name):
        return
    if not await _notify_if_missing_category_permissions(member, creator_channel, category, guild_name):
        return

    #  ========== 4. Collate overwrites ==========
    collate_temp_channel_overwrites(overwrites, bot.user, member)
    if not await _notify_if_invalid_create_overwrites(
        member, creator_channel, category, overwrites, guild_name
    ):
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

    #  ========== 7. Update channel named based on naming scheme (slow, done last) ==========
    channel_name = create_temp_channel_name(bot, new_temp_channel, db_creator_channel_info=db_info)
    logger.debug(f"Generated temp channel name '{channel_name}' for {new_temp_channel.id} in guild '{guild_name}'")
    control_view = await _finalize_temp_channel(
        bot, new_temp_channel, member, db_info, channel_name, guild_name, creator_channel
    )
    if control_view is None:
        return

    # 8. ======== Send DM to Owner ==========
    await dm_user_on_create(bot, new_temp_channel, member, control_view)

    # 9. ======== Send Logs ==========
    await send_temp_channel_create_logs(bot, new_temp_channel, member, guild_name)
