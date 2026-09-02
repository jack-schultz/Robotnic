import logging
import random
import discord
import asyncio
from cogs.manage_vcs.update_name import update_channel_name_and_control_msg
from api.stats import stats

logger = logging.getLogger(__name__)


async def create_tasks(bot):
    if bot._background_tasks_started:
        logger.debug("Background tasks already running, skipping duplicate startup")
        return []

    bot._background_tasks_started = True
    tasks = []

    # These are the functions in this file that will run periodically in bot.loop
    functions = [update_temp_channel_names, update_presence, clear_empty_temp_channels]
    for func in functions:
        tasks.append(bot.loop.create_task(func(bot)))

    logger.debug(f"Created {len(tasks)} coroutine tasks")
    return tasks


# Technically shouldn't be required as manage_vcs.update_name.update_channel_name_and_control_msg is run every time a user leaves a vc
# This is here in case of desync. Hopefully can be removed once the bot is tested properly
async def update_temp_channel_names(bot):
    await bot.wait_until_ready()  # Ensure the bot is fully connected
    while not bot.is_closed():  # Run on a schedule
        try:
            logger.debug(f"Updating all temp channel names on schedule")
            temp_channel_ids = bot.repos.temp_channels.get_ids()
            await update_channel_name_and_control_msg(bot, temp_channel_ids)
        except Exception as e:
            logger.error(f"Error in {__name__} task: {e}")
        await asyncio.sleep(300 + random.uniform(0, 30))


async def update_presence(bot):
    await bot.wait_until_ready()  # Ensure the bot is fully connected
    while not bot.is_closed():  # Run on a schedule
        try:
            status_text = bot.settings["status"].get("text", "")

            # Create variables if needed
            server_count = len(bot.guilds)

            # Calculate user count, could need ratelimiting in future? idk
            member_count = 0
            for guild in bot.guilds:
                member_count += guild.member_count

            # Get count of creator channels
            creator_count = len(bot.repos.creator_channels.get_ids())

            # Get count of temp channels
            temp_channel_count = len(bot.repos.temp_channels.get_ids())

            # Format from settings
            status = status_text.format(**locals())
            await bot.change_presence(activity=discord.Game(status))
            logger.debug(f"Updated presence to \'{status}\'")

            # Post guild count to TopGG
            if bot.topgg_client:
                await bot.topgg_client.post_guild_count()
                logger.debug(f"Posted Guild Count to TOPGG; {server_count}")

            # Update Stats object for API
            with stats.lock:
                stats.guilds = server_count
                stats.users = member_count
                stats.creators = creator_count
                stats.channels = temp_channel_count

            # Display embed ratelimiting stats periodically for debugging
            embed_stats = bot.EmbedUpdateScheduler.stats
            logger.debug(
                f"Embed scheduler stats: scheduled={embed_stats['scheduled']} "
                f"edited={embed_stats['edited']} skipped={embed_stats['skipped']} "
                f"rate_limited={embed_stats['rate_limited']}"
            )

        except Exception as e:
            logger.error(f"Error in {__name__} task: {e}")

        await asyncio.sleep(3600)  # 1 hour (3600 seconds)


# Known bug that if this triggers while a user is creating a temp channel and is yet to be moved, this may delete the channel and cause an error
async def clear_empty_temp_channels(bot):
    await bot.wait_until_ready()  # Ensure the bot is fully connected
    while not bot.is_closed():  # Run on a schedule
        try:
            logger.debug("Clearing empty temp channels...")

            # Clean up empty temp channels
            temp_channel_ids = bot.repos.temp_channels.get_ids()
            for channel_id in temp_channel_ids:
                channel = bot.get_channel(channel_id)
                if channel is None:
                    logger.warning(f"Removing unfound/deleted temp channel from database")
                    bot.repos.temp_channels.remove(channel_id)
                    continue

                # Having member intent should mean this is not needed
                if not channel.guild.chunked:  # Only chunk if not already done
                    logger.debug(f"Fetching all members for guild {channel.guild.name} to populate cache")
                    await channel.guild.chunk()

                if len(channel.members) == 0:
                    logger.debug(f"Deleting empty temp channel '{channel.name}' in guild '{channel.guild.name}'")
                    try:
                        await channel.delete()
                        bot.repos.temp_channels.remove(channel.id)
                    except discord.NotFound:
                        bot.repos.temp_channels.remove(channel.id)
                        logger.debug(
                            f"Empty temp channel {channel.id} already deleted in guild '{channel.guild.name}', removed db entry"
                        )
                    except discord.Forbidden as e:
                        logger.warning(
                            f"Permission error deleting empty temp channel {channel.id} in guild '{channel.guild.name}': {e}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to delete empty temp channel {channel.id} in guild '{channel.guild.name}': {e}"
                        )

        except Exception as e:
            logger.error(f"Error in {__name__} task: {e}")

        await asyncio.sleep(300)  # 5 minutes (300 seconds)
