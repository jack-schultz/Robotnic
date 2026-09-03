import logging
import discord
from cogs.manage_vcs.notifications import send_temp_channel_remove_logs

logger = logging.getLogger(__name__)


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

    await send_temp_channel_remove_logs(bot, old_temp_channel, member, guild_name)
