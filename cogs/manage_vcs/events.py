import logging
from cogs.manage_vcs.lifecycle import create_on_join, delete_on_leave
from cogs.manage_vcs.update_name import update_channel_name_and_control_msg

logger = logging.getLogger(__name__)


async def handle_voice_state_update(bot, member, before, after):
    # Filter out normal updates when not switching channels
    if before is not None and after is not None:
        if before.channel == after.channel:
            return

    if after.channel:  # If a user joined a channel
        creator_channel_ids = bot.repos.creator_channels.get_ids()
        if after.channel.id in creator_channel_ids:  # Filter to creator channels
            logger.debug(f"Routing {member} to create_on_join for creator channel {after.channel.id} in guild '{member.guild.name}'")
            await create_on_join(member, before, after, bot)

    if before.channel:  # If a user left a channel
        temp_channel_ids = bot.repos.temp_channels.get_ids(guild_id=before.channel.guild.id)
        if before.channel.id in temp_channel_ids:  # Filter to temp channels
            logger.debug(f"Routing {member} leave from temp channel {before.channel.id} to delete_on_leave in guild '{before.channel.guild.name}'")
            await delete_on_leave(member, before, after, bot)

            # Update channel names of all temp channels in the guild
            logger.debug(f"Updating temp channel names in guild '{before.channel.guild.name}' because a user left a temp_vc")
            await update_channel_name_and_control_msg(bot, temp_channel_ids)


async def handle_presence_update(bot, before, after):
    if after.voice is None or after.voice.channel is None:
        return
    temp_channel = after.voice.channel
    if temp_channel.id not in bot.repos.temp_channels.get_ids(guild_id=after.guild.id):
        return

    logger.debug(f"Updating {temp_channel.name} due to activity change in guild '{temp_channel.guild.name}'")
    await update_channel_name_and_control_msg(bot, [temp_channel.id])


async def handle_guild_channel_delete(bot, channel):
    if channel.id not in bot.repos.temp_channels.get_ids():
        return
    logger.debug(f"Removing temp channel {channel.id} from database after channel delete in guild '{channel.guild.name}'")
    bot.repos.temp_channels.remove(channel.id)
