from discord.ext import commands
from cogs.control_vc.views.control_view import ControlView


class Control_Vc_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(ControlView.for_persistence(self.bot))


def setup(bot):
    bot.add_cog(Control_Vc_cog(bot))
