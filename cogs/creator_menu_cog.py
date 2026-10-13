import logging
import discord
from discord.ext import commands
from cogs.creator_menu.embeds import ListCreatorsEmbed
from cogs.creator_menu.views import CreateView
from config.i18n import t, command_kwargs

logger = logging.getLogger(__name__)


class CreatorMenuCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(**command_kwargs("commands.setup"))
    @discord.default_permissions(manage_channels=True)
    async def setup(self, ctx):
        if not ctx.author.guild_permissions.manage_channels:
            lang = self.bot.repos.guild_settings.get_language(ctx.guild.id)
            return await ctx.send_response(t("setup.missing_permission", lang, mention=ctx.author.mention))

        creator_channel_ids = self.bot.repos.creator_channels.get_ids(ctx.guild.id)
        for channel_id in creator_channel_ids:
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                logger.warning(f"Removing unfound/deleted creator channel {channel_id} from database in guild '{ctx.guild.name}'")
                self.bot.repos.creator_channels.remove(channel_id)

        embeds = [ListCreatorsEmbed(guild=ctx.guild, bot=self.bot)]
        view = CreateView(ctx=ctx, bot=self.bot)
        message = await ctx.send_response(f"{ctx.author.mention}", embeds=embeds, view=view)  # , ephemeral=True)
        view.message = message


def setup(bot):
    bot.add_cog(CreatorMenuCog(bot))
