import discord
from discord.ext import commands
from cogs.manage_vcs.events import handle_voice_state_update, handle_presence_update, handle_guild_channel_delete
from cogs.manage_vcs.views.dm_owner_button import AcknowledgeButtonView


class ManageVcsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(AcknowledgeButtonView(self.bot))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        await handle_voice_state_update(self.bot, member, before, after)

    # If user's activity changes while in a temp vc, update its name
    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        await handle_presence_update(self.bot, before, after)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await handle_guild_channel_delete(self.bot, channel)


def setup(bot):
    bot.add_cog(ManageVcsCog(bot))
