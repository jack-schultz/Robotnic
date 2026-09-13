import discord
from discord.ext import commands
from cogs.control_vc import context_menus


class Control_Vc_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # RIGHT CLICK USER -> APPS -> BAN USER
    @discord.user_command(name="Ban User from VC")
    async def ban_user(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member
    ):
        await context_menus.ban_user(self.bot, ctx, user)

    # RIGHT CLICK USER -> APPS -> ALLOW USER
    @discord.user_command(name="Allow User to VC")
    async def allow_user(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member
    ):
        await context_menus.allow_user(self.bot, ctx, user)

    @discord.user_command(name="Mute User")
    async def mute_user(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member
    ):
        await context_menus.mute_user(self.bot, ctx, user)

    @discord.user_command(name="Deafen User")
    async def deafen_user(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member
    ):
        await context_menus.deafen_user(self.bot, ctx, user)

    @discord.user_command(name="Unmute & Undeafen User")
    async def unmute_and_undeafen_user(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member
    ):
        await context_menus.unmute_and_undeafen_user(self.bot, ctx, user)


def setup(bot):
    bot.add_cog(Control_Vc_cog(bot))
