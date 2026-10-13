import discord
from cogs.control_vc.enums import Action
from cogs.control_vc.member_actions.handler.actions import handle_action
from config.i18n import t


class _MemberSelectView(discord.ui.View):
    def __init__(self, bot, channel, timeout):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.channel = channel
        self.message = None
        self.lang = bot.repos.guild_settings.get_language(channel.guild.id)

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
        self.ban_select_callback.placeholder = t("control.members.ban_placeholder", self.lang)
        self.allow_select_callback.placeholder = t("control.members.allow_placeholder", self.lang)

    @discord.ui.mentionable_select(min_values=0, max_values=25)
    async def ban_select_callback(self, select, interaction: discord.Interaction):
        await handle_action(self.bot, interaction, Action.BAN, select.values, channel=self.channel)

    @discord.ui.mentionable_select(min_values=0, max_values=25)
    async def allow_select_callback(self, select, interaction: discord.Interaction):
        await handle_action(self.bot, interaction, Action.ALLOW, select.values, channel=self.channel)

    async def send_initial_message(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=t("control.members.ban_title", self.lang),
            description=t("control.members.ban_description", self.lang),
            color=0x00FF00,
        )
        embed.set_footer(text=t("control.members.selection_footer", self.lang))
        await self._send(interaction, embed)


class MuteUserView(_MemberSelectView):
    def __init__(self, bot, channel):
        super().__init__(bot, channel, timeout=60)
        self.mute_select_callback.placeholder = t("control.members.mute_placeholder", self.lang)
        self.unmute_select_callback.placeholder = t("control.members.unmute_placeholder", self.lang)

    @discord.ui.user_select(min_values=0, max_values=25)
    async def mute_select_callback(self, select, interaction: discord.Interaction):
        await handle_action(self.bot, interaction, Action.MUTE, select.values, channel=self.channel)

    @discord.ui.user_select(min_values=0, max_values=25)
    async def unmute_select_callback(self, select, interaction: discord.Interaction):
        await handle_action(self.bot, interaction, Action.UNMUTE, select.values, channel=self.channel)

    async def send_initial_message(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=t("control.members.mute_title", self.lang),
            description=t("control.members.mute_description", self.lang),
            color=0x00FF00,
        )
        embed.set_footer(text=t("control.members.selection_footer", self.lang))
        await self._send(interaction, embed)


class DeafenUserView(_MemberSelectView):
    def __init__(self, bot, channel):
        super().__init__(bot, channel, timeout=60)
        self.deafen_select_callback.placeholder = t("control.members.deafen_placeholder", self.lang)
        self.undeafen_select_callback.placeholder = t("control.members.undeafen_placeholder", self.lang)

    @discord.ui.user_select(min_values=0, max_values=25)
    async def deafen_select_callback(self, select, interaction: discord.Interaction):
        await handle_action(self.bot, interaction, Action.DEAFEN, select.values, channel=self.channel)

    @discord.ui.user_select(min_values=0, max_values=25)
    async def undeafen_select_callback(self, select, interaction: discord.Interaction):
        await handle_action(self.bot, interaction, Action.UNDEAFEN, select.values, channel=self.channel)

    async def send_initial_message(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=t("control.members.deafen_title", self.lang),
            description=t("control.members.deafen_description", self.lang),
            color=0x00FF00,
        )
        embed.set_footer(text=t("control.members.selection_footer", self.lang))
        await self._send(interaction, embed)
