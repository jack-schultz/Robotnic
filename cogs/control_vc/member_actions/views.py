import discord

from cogs.control_vc.enums import Action
from cogs.control_vc.member_actions.handler.actions import handle_action


class _MemberSelectView(discord.ui.View):
    def __init__(self, bot, channel, timeout):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.channel = channel
        self.message = None

    async def _send(self, interaction, embed):
        self.message = await interaction.followup.send(
            embed=embed,
            view=self,
            ephemeral=True,
            wait=True,
        )

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except discord.NotFound:
                pass


class BanUserView(_MemberSelectView):
    def __init__(self, bot, channel):
        super().__init__(bot, channel, timeout=300)

    @discord.ui.mentionable_select(placeholder="Select members or roles to ban", min_values=0, max_values=25)
    async def ban_select_callback(self, select, interaction: discord.Interaction):
        await handle_action(self.bot, interaction, Action.BAN, select.values, channel=self.channel)

    @discord.ui.mentionable_select(placeholder="Select members or roles to allow", min_values=0, max_values=25)
    async def allow_select_callback(self, select, interaction: discord.Interaction):
        await handle_action(self.bot, interaction, Action.ALLOW, select.values, channel=self.channel)

    async def send_initial_message(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔨 Manage access to your channel",
            description=(
                "Use the menus below to ban or allow members/roles.\n"
                "Banned users cannot view or connect to the channel."
            ),
            color=0x00FF00,
        )
        embed.set_footer(text="You have 60 seconds to make selections.")
        await self._send(interaction, embed)


class MuteUserView(_MemberSelectView):
    def __init__(self, bot, channel):
        super().__init__(bot, channel, timeout=60)

    @discord.ui.user_select(placeholder="Select members to mute", min_values=0, max_values=25)
    async def mute_select_callback(self, select, interaction: discord.Interaction):
        await handle_action(self.bot, interaction, Action.MUTE, select.values, channel=self.channel)

    @discord.ui.user_select(placeholder="Select members to unmute", min_values=0, max_values=25)
    async def unmute_select_callback(self, select, interaction: discord.Interaction):
        await handle_action(self.bot, interaction, Action.UNMUTE, select.values, channel=self.channel)

    async def send_initial_message(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔇 Mute or unmute members",
            description="Use the menus below to server-mute or unmute members in this channel.\n",
            color=0x00FF00,
        )
        embed.set_footer(text="You have 60 seconds to make selections.")
        await self._send(interaction, embed)


class DeafenUserView(_MemberSelectView):
    def __init__(self, bot, channel):
        super().__init__(bot, channel, timeout=60)

    @discord.ui.user_select(placeholder="Select members to deafen", min_values=0, max_values=25)
    async def deafen_select_callback(self, select, interaction: discord.Interaction):
        await handle_action(self.bot, interaction, Action.DEAFEN, select.values, channel=self.channel)

    @discord.ui.user_select(placeholder="Select members to undeafen", min_values=0, max_values=25)
    async def undeafen_select_callback(self, select, interaction: discord.Interaction):
        await handle_action(self.bot, interaction, Action.UNDEAFEN, select.values, channel=self.channel)

    async def send_initial_message(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔕 Deafen or undeafen members",
            description="Use the menus below to server-deafen or undeafen members in this channel.\n",
            color=0x00FF00,
        )
        embed.set_footer(text="You have 60 seconds to make selections.")
        await self._send(interaction, embed)
