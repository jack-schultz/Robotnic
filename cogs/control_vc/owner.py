import logging
from cogs.manage_vcs.owner_role import remove_owner_role, give_owner_role
from cogs.manage_vcs.owner_prefix import remove_owner_prefix, give_owner_prefix

logger = logging.getLogger(__name__)


async def claim_or_verify_owner(bot, channel, member):
    if member not in channel.members:
        logger.debug(
            f"User '{member}' interacted with control that they are not connected to "
            f"in guild '{channel.guild.name}'."
        )
        return False, f"You are not connected to this voice channel {member.mention}!"

    connected_user_ids = [member.id for member in channel.members]
    owner_id = bot.repos.temp_channels.get_info(channel.id).owner_id

    # If owner isn't connected, make interacting user owner and update info embed
    if owner_id is None or owner_id not in connected_user_ids:
        # Update ownership first so prefix/role removal can see they are no longer an owner
        bot.repos.temp_channels.set_owner_id(channel.id, member.id)

        if owner_id is not None:
            prev_owner = channel.guild.get_member(owner_id)
            await remove_owner_role(bot, prev_owner)
            await remove_owner_prefix(bot, prev_owner)

        await give_owner_role(bot, member)
        await give_owner_prefix(bot, member)
        await bot.EmbedUpdateScheduler.schedule(channel)

    # If owner is connected and isn't interacting user, deny
    elif owner_id != member.id:
        logger.debug(
            f"User '{member}' interacted with control that they don't own "
            f"in guild '{channel.guild.name}'."
        )
        return False, f"You do not own this temporary channel {member.mention}!"

    return True, None


async def is_owner(view, interaction):
    ok, error = await claim_or_verify_owner(
        view.bot, interaction.channel, interaction.user
    )
    if not ok:
        await interaction.response.send_message(
            error, ephemeral=True, delete_after=15
        )
        return False
    return True
