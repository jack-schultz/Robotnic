import logging
import asyncio
import time
from cogs.control_vc.embed_scheduler import schedule_info_embed
from cogs.manage_vcs.create_name import create_temp_channel_name

logger = logging.getLogger(__name__)


# Updates channel name to match its creator's template.
# Updates Control message's info embed to reflect true data
async def update_channel_name_and_control_msg(bot, temp_channel_ids):
    sample_channel = bot.get_channel(temp_channel_ids[0]) if temp_channel_ids else None
    guild_name = sample_channel.guild.name if sample_channel else "unknown"
    logger.debug(
        f"Updating {len(temp_channel_ids)} temp channel names & control msgs in guild '{guild_name}'..."
    )
    start = time.perf_counter()

    # Fixes any badly ordered channel count in the db
    # name update will reflect the db, so we fix it first
    bot.repos.temp_channels.fix_count()

    async def update(temp_channel_id):
        temp_channel = bot.get_channel(temp_channel_id)
        db_temp_channel_info = bot.repos.temp_channels.get_info(temp_channel_id)
        channel_guild_name = temp_channel.guild.name if temp_channel else None
        if channel_guild_name is None and db_temp_channel_info is not None:
            guild = bot.get_guild(db_temp_channel_info.guild_id)
            channel_guild_name = guild.name if guild else "unknown"
        if temp_channel is None or db_temp_channel_info is None:
            if db_temp_channel_info is not None and temp_channel is None:
                logger.debug(
                    f"Temp channel {temp_channel_id} in guild '{channel_guild_name or 'unknown'}' "
                    f"exists in database but channel was not found, removing stale row."
                )
                bot.repos.temp_channels.remove(temp_channel_id)
            else:
                logger.debug(
                    f"Skipping temp channel {temp_channel_id} in guild '{channel_guild_name or 'unknown'}': "
                    f"channel or db info not found."
                )
            return
        if db_temp_channel_info.is_renamed:
            logger.debug(
                f"Skipping temp channel {temp_channel_id} in guild '{channel_guild_name}': manually renamed."
            )
            return
        if not temp_channel or not db_temp_channel_info.creator_id:  # Filter so only channels in the temp_channels db continue
            logger.warning(
                f"Skipping temp channel {temp_channel_id} in guild '{channel_guild_name}': missing channel or creator_id."
            )
            return

        new_channel_name = None
        if not db_temp_channel_info.is_renamed:
            new_channel_name = create_temp_channel_name(
                bot, temp_channel, db_temp_channel_info=db_temp_channel_info
            )

            # Rename channel if not renamed and new name is different
            if temp_channel.name != new_channel_name:
                if len(temp_channel.members) > 0:  # If empty it is going to be deleted, ignore
                    logger.debug(f"Renaming {temp_channel.name} to {new_channel_name} in guild '{channel_guild_name}'")
                    await bot.TempChannelRenamer.schedule(temp_channel, new_channel_name)
                else:
                    logger.debug(
                        f"Skipping rename for empty temp channel {temp_channel_id} in guild '{channel_guild_name}', pending deletion."
                    )
            else:
                logger.debug(
                    f"Temp channel {temp_channel.name} ({temp_channel_id}) in guild '{channel_guild_name}' "
                    f"name unchanged ('{new_channel_name}'), skipping rename."
                )

        # Update control message
        await bot.EmbedUpdateScheduler.schedule(temp_channel, title=new_channel_name)

    # Run all updates concurrently
    tasks = (update(channel_id) for channel_id in temp_channel_ids)
    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        logger.warning(
            f"Unhandled error in update_channel_name_and_control_msg in guild '{guild_name}': {e}"
        )

    end = time.perf_counter()
    duration = end - start
    logger.debug(f"Temp channel name update completed in guild '{guild_name}' in {duration:.4f} seconds")
