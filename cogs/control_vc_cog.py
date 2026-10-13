import discord
from discord.ext import commands
from cogs.control_vc.member_actions import context_menus
from config.i18n import t, localizations


class Control_Vc_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # RIGHT CLICK USER -> APPS -> BAN USER
    @discord.user_command(name=t("commands.ban_user.name"), name_localizations=localizations("commands.ban_user.name"))
    async def ban_user(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member
    ):
        await context_menus.ban_user(self.bot, ctx, user)

    # RIGHT CLICK USER -> APPS -> ALLOW USER
    @discord.user_command(name=t("commands.allow_user.name"), name_localizations=localizations("commands.allow_user.name"))
    async def allow_user(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member
    ):
        await context_menus.allow_user(self.bot, ctx, user)

    @discord.user_command(name=t("commands.mute_user.name"), name_localizations=localizations("commands.mute_user.name"))
    async def mute_user(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member
    ):
        await context_menus.mute_user(self.bot, ctx, user)

    @discord.user_command(name=t("commands.deafen_user.name"), name_localizations=localizations("commands.deafen_user.name"))
    async def deafen_user(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member
    ):
        await context_menus.deafen_user(self.bot, ctx, user)

    @discord.user_command(name=t("commands.unmute_and_undeafen_user.name"), name_localizations=localizations("commands.unmute_and_undeafen_user.name"))
    async def unmute_and_undeafen_user(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member
    ):
        await context_menus.unmute_and_undeafen_user(self.bot, ctx, user)


def setup(bot):
    bot.add_cog(Control_Vc_cog(bot))
