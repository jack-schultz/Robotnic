import logging
import discord

logger = logging.getLogger(__name__)


async def close(bot):
    logger.info(f'Logging out {bot.user}')

    # Update all control messages with a disabled button saying its expired
    for temp_channel_id in bot.repos.temp_channels.get_ids():
        temp_channel = bot.get_channel(temp_channel_id)
        if temp_channel is None:
            continue
        # Searches first 10 messages for first send by the bot. This will almost always be the creator
        try:
            async for control_message in temp_channel.history(limit=10, oldest_first=True):
                if control_message.author.id == bot.user.id:
                    # Create a new view with one disabled button
                    view = discord.ui.View()
                    view.add_item(
                        discord.ui.Button(
                            label="This control message has expired",
                            style=discord.ButtonStyle.secondary,
                            disabled=True
                        )
                    )
                    # Edit the message to show the new view
                    await control_message.edit(view=view)
                    break
        except discord.NotFound:
            logger.debug(f"Control message already gone for temp channel {temp_channel_id} during shutdown")
        except Exception as e:
            logger.warning(f"Failed to expire control message for temp channel {temp_channel_id}: {e}")

    if bot.BotLogService:
        await bot.BotLogService.send(event="stop", message=f"Bot {bot.user.mention} stopping.")
