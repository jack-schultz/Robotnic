import logging
import datetime
import discord
from cogs.control_vc.views.control_view import ControlView
from cogs.manage_vcs.create_name import create_temp_channel_name

logger = logging.getLogger(__name__)


def _get_child_category(db_info, creator_channel, bot, guild_name):
    if db_info.child_category_id != 0:
        category = bot.get_channel(db_info.child_category_id)
        if category is None:
            logger.warning(
                f"Configured child category {db_info.child_category_id} not found for creator channel {creator_channel.id} in guild '{guild_name}'"
            )
        logger.debug(
            f"Using configured child category {db_info.child_category_id} "
            f"({category.name if category else 'not found'}) for creator channel {creator_channel.id} in guild '{guild_name}'"
        )
    else:
        category = creator_channel.category
        logger.debug(
            f"Using creator channel category "
            f"({category.name if category else 'none'}) for creator channel {creator_channel.id} "
            f"in guild '{guild_name}'"
        )
    return category


def _get_child_overwrites(db_info, creator_channel, category, guild_name):
    # 0 -> no overwrites
    # 1 -> overwrites from creator
    # 2 -> overwrites from category
    if db_info.child_overwrites == 1:
        overwrites = creator_channel.overwrites
        logger.debug(f"Using creator channel overwrites for temp channel in {creator_channel.id} in guild '{guild_name}'")
    elif db_info.child_overwrites == 2:
        if category:
            overwrites = category.overwrites
            logger.debug(f"Using category overwrites from {category.name} for temp channel in {creator_channel.id} in guild '{guild_name}'")
        else:
            overwrites = creator_channel.overwrites
            logger.warning(
                f"No category available for overwrite source, falling back to creator channel overwrites for {creator_channel.id} in guild '{guild_name}'"
            )
    else:
        overwrites = {}
        logger.debug(f"Using no inherited overwrites for temp channel in {creator_channel.id} in guild '{guild_name}'")
    return overwrites


def _collate_temp_channel_overwrites(overwrites, bot_user, member):
    overwrites[bot_user] = discord.PermissionOverwrite(
        view_channel=True,
        manage_channels=True,
        send_messages=True,
        manage_messages=True,
        read_message_history=True,
        connect=True,
        move_members=True,
    )
    overwrites[member] = discord.PermissionOverwrite(
        view_channel=True,
        send_messages=True,
        read_message_history=True,
        connect=True,
    )


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


async def _notify_if_missing_guild_permissions(member, creator_channel, category, guild_name):
    permissions_to_check = [
        "manage_channels",
        "manage_roles",
        "view_channel",
        "send_messages",
        "connect",
        "move_members",
        "manage_messages",
        "read_message_history"
    ]
    has_all_perms = True
    missing_permissions = []
    for perm in permissions_to_check:
        has_perm = getattr(member.guild.me.guild_permissions, perm, False)
        if not has_perm:
            has_all_perms = False
            missing_permissions.append(perm)

    if not has_all_perms:
        logger.warning(
            f"Missing guild permissions to create temp channel for {member} in guild '{guild_name}', aborting. "
            f"Missing: {', '.join(missing_permissions)}"
        )
        logger.debug(
            f"Notified {member} of missing permissions in guild '{guild_name}'"
        )
        embed = discord.Embed()
        embed.add_field(name="Required",
                        value="`view_channel`, `manage_channels`, `manage_roles`, `send_messages`, `manage_messages`, `read_message_history`, `connect`, `move_members`")
        embed.add_field(name="Missing",
                        value=f"{', '.join(f'`{perm}`' for perm in missing_permissions)}")
        response_text = f"Sorry {member.mention}, I require the following permissions."
        if category:
            response_text = response_text + f"Make sure they are not overwritten by the category (In this case `{category.name}`)."
        await creator_channel.send(response_text, embed=embed, delete_after=300)
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
        logger.warning(
            f"Permission error creating temp channel in category in guild '{guild_name}', "
            f"notifying user of missing permissions. {e}"
        )
        response_text = f"Sorry {member.mention}, I do not have permission to create a channel in the desired category"
        if category:
            response_text = response_text + f" (`{category.name}`)."
        else:
            response_text = response_text + "."
        try:
            await creator_channel.send(response_text, delete_after=300)
        except discord.Forbidden as e:
            logger.warning(
                f"Could not notify {member} of missing permissions in creator channel {creator_channel.id} in guild '{guild_name}'. {e}"
            )
        except Exception as e:
            logger.warning(
                f"Error notifying {member} of missing permissions in guild '{guild_name}'. {e}"
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


async def _finalize_temp_channel(bot, temp_channel, member, db_info, channel_name, guild_name):
    try:
        # Could use bot.TempChannelRenamer to avoid rate-limit problems but this does not support user limit yet
        # Fine to use without scheduling as rate limit bucket will never be full immediately after creation
        await temp_channel.edit(
            name=channel_name,
            user_limit=db_info.user_limit,
        )

        # Send control message in channel chat
        view = ControlView(bot, temp_channel)
        await view.send_initial_message(member, channel_name=channel_name)
        logger.debug(f"Finalized temp channel {temp_channel.id} as '{channel_name}' with control message in guild '{guild_name}'")
    except Exception as e:
        logger.warning(f"Error finalizing creation of voice channel in guild '{guild_name}', handled. {e}")


async def _send_temp_channel_create_logs(bot, temp_channel, member, guild_name):
    embed = discord.Embed(
        title="TempChannel Create",
        description="",
        color=discord.Color.green()
    )
    embed.add_field(name="Channel",
                    value=f"`{temp_channel.name}` (`{temp_channel.id}`)",
                    inline=False)
    embed.add_field(name="User",
                    value=f"`{member}` (`{member.id}`)",
                    inline=False)
    embed.timestamp = datetime.datetime.now()
    await bot.GuildLogService.send(event="channel_create", guild=temp_channel.guild, message=f"", embed=embed)
    await bot.BotLogService.send(event="channel_create", message=f"Temp Channel (`{temp_channel.name}`) was made in server (`{member.guild.name}`) by user (`{member}`)")
    logger.debug(f"Sent create logs for temp channel {temp_channel.name} ({temp_channel.id}) in guild '{guild_name}'")


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
    category = _get_child_category(db_info, creator_channel, bot, guild_name)
    overwrites = _get_child_overwrites(db_info, creator_channel, category, guild_name)

    #  ========== 3. Notify of missing permissions ==========
    if not await _notify_if_missing_guild_permissions(member, creator_channel, category, guild_name):
        return

    #  ========== 4. Collate overwrites ==========
    _collate_temp_channel_overwrites(overwrites, bot.user, member)

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
    await _finalize_temp_channel(bot, new_temp_channel, member, db_info, channel_name, guild_name)

    # 8. ======== Send DM to Owner ==========

    # 9. ======== Send Logs ==========
    await _send_temp_channel_create_logs(bot, new_temp_channel, member, guild_name)


async def delete_on_leave(member, before, after, bot):
    old_temp_channel = before.channel
    guild_name = member.guild.name
    logger.debug(f"{member} left temp channel {old_temp_channel.name} ({old_temp_channel.id}) in guild '{guild_name}'")

    if len(old_temp_channel.members) >= 1:
        logger.debug(f"Temp channel {old_temp_channel.id} still has {len(old_temp_channel.members)} member(s) in guild '{guild_name}', skipping delete")
        return

    logger.debug(f"Left temp channel is empty in guild '{guild_name}'. Deleting...")

    try:
        await old_temp_channel.delete()
        bot.repos.temp_channels.remove(old_temp_channel.id)
        logger.debug(f"Deleted {old_temp_channel.name} in guild '{guild_name}'")

    except discord.NotFound as e:
        bot.repos.temp_channels.remove(old_temp_channel.id)
        logger.debug(f"Channel not found removing entry in db in guild '{guild_name}', handled. {e}")
        return

    except discord.Forbidden as e:
        logger.warning(
            f"Permission error removing temp channel {old_temp_channel.id} in guild '{guild_name}', "
            f"notifying user of missing permissions. {e}"
        )
        await old_temp_channel.send(f"Sorry {member.mention}, I do not have permission to delete this channel.", delete_after=300)
        return

    except Exception as e:
        logger.error(f"Unknown error removing temp channel in guild '{guild_name}'. {e}")
        return

    embed = discord.Embed(
        title="TempChannel Removed",
        description="",
        color=discord.Color.orange()
    )
    embed.add_field(name="Channel",
                    value=f"`{old_temp_channel.name}` (`{old_temp_channel.id}`)",
                    inline=False)
    embed.add_field(name="Last Connected User",
                    value=f"`{member}` (`{member.id}`)",
                    inline=False)
    embed.timestamp = datetime.datetime.now()
    await bot.GuildLogService.send(event="channel_remove", guild=member.guild, message=f"", embed=embed)
    await bot.BotLogService.send(event="channel_remove", message=f"Temp Channel was removed in server (`{member.guild.name}`) by user (`{member}`)")
    logger.debug(f"Sent remove logs for temp channel {old_temp_channel.name} ({old_temp_channel.id}) in guild '{guild_name}'")
