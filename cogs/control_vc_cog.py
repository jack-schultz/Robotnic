from discord.ext import commands
from cogs.control_vc.views.control_view import ControlView
import logging
import discord

logger = logging.getLogger(__name__)


class Control_Vc_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        db_channels = self.bot.repos.temp_channels.get_ids()
        logger.info(f"Registering {len(db_channels)} persistent control views")

        view = ControlView(self.bot, channel)
        self.bot.add_view(view)

        for channel_id in db_channels:
            channel = self.bot.get_channel(channel_id)

            if channel is None:
                continue

            logger.info(f"Registering {channel.name}")



            try:
                async for message in channel.history(limit=10, oldest_first=True):
                    if message.author.id == self.bot.user.id and message.components:
                        view.control_message = message
                        await message.edit(view=view, embeds=message.embeds)
                        break
            except discord.NotFound:
                logger.debug(f"Control message already gone for temp channel {channel_id} during view registration")
            except Exception as e:
                logger.warning(f"Failed to refresh control message for temp channel {channel_id}: {e}")

        self.bot.add_view(ControlView(self.bot))


def setup(bot):
    bot.add_cog(Control_Vc_cog(bot))
