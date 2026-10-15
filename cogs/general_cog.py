import discord
from discord.ext import commands
from cogs.general.embeds import DonateEmbed, HelpEmbed
from cogs.general.views import ButtonsView
from config.i18n import t, command_kwargs


class GeneralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(**command_kwargs("commands.ping"))
    @discord.default_permissions(manage_channels=True)
    async def ping(self, ctx):
        await ctx.respond(t("general.ping", self.bot.repos.guild_settings.get_language(ctx.guild_id), latency=self.bot.latency))

    @discord.slash_command(**command_kwargs("commands.help"))
    async def help(self, ctx):
        lang = self.bot.repos.guild_settings.get_language(ctx.guild_id)
        embeds = [
            HelpEmbed(lang)
        ]
        await ctx.respond(f"", embeds=embeds, view=ButtonsView(lang))

    @discord.slash_command(**command_kwargs("commands.donate"))
    async def donate(self, ctx):
        lang = self.bot.repos.guild_settings.get_language(ctx.guild_id)
        await ctx.respond(f"", embeds=[DonateEmbed(lang)], view=ButtonsView(lang))

    # Alias to /donate
    @discord.slash_command(**command_kwargs("commands.support"))
    async def support(self, ctx):
        await self.donate.callback(self, ctx)

    # Alias to /donate
    @discord.slash_command(**command_kwargs("commands.website"))
    async def website(self, ctx):
        await self.donate.callback(self, ctx)


def setup(bot):
    bot.add_cog(GeneralCog(bot))
