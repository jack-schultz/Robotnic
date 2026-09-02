import discord
from discord.ext import commands
from cogs.general.embeds import DonateEmbed, HelpEmbed
from cogs.general.views import ButtonsView


class GeneralCCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(description="Responds with bot latency.")
    @discord.default_permissions(manage_channels=True)
    async def ping(self, ctx):
        await ctx.respond(f"Pong! Latency is {self.bot.latency}")

    @discord.slash_command(description="Get help using Robotnic or support the creator.")
    async def help(self, ctx):
        embeds = [
            HelpEmbed()
        ]
        await ctx.respond(f"", embeds=embeds, view=ButtonsView())

    @discord.slash_command(description="Get support using Robotnic or support the creator.")
    async def donate(self, ctx):
        await ctx.respond(f"", embeds=[DonateEmbed()], view=ButtonsView())

    # Alias to /donate
    @discord.slash_command(description="Support the creator of Robotnic.")
    async def support(self, ctx):
        await self.donate.callback(self, ctx)

    # Alias to /donate
    @discord.slash_command(description="Support the creator of Robotnic.")
    async def website(self, ctx):
        await self.donate.callback(self, ctx)


def setup(bot):
    bot.add_cog(GeneralCCog(bot))
