import logging

import discord

logger = logging.getLogger(__name__)


class MuteUserView(discord.ui.View):
    def __init__(self, bot, channel):
        super().__init__(timeout=60)
        self.bot = bot
        self.channel = channel
        self.message = None

    async def send_initial_message(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔇 Mute or unmute members",
            description=(
                "Use the menus below to server-mute or unmute members in this channel.\n"
            ),
            color=0x00FF00,
        )
        embed.set_footer(text="You have 60 seconds to make selections.")
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

    @discord.ui.user_select(
        placeholder="Select members to mute",
        min_values=0,
        max_values=25,
    )
    async def mute_select_callback(self, select, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # Add logic and response

    @discord.ui.user_select(
        placeholder="Select members to unmute",
        min_values=0,
        max_values=25,
    )
    async def unmute_select_callback(self, select, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # Add logic and response


class DeafenUserView(discord.ui.View):
    def __init__(self, bot, channel):
        super().__init__(timeout=60)
        self.bot = bot
        self.channel = channel
        self.message = None

    async def send_initial_message(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔕 Deafen or undeafen members",
            description=(
                "Use the menus below to server-deafen or undeafen members in this channel.\n"
            ),
            color=0x00FF00,
        )
        embed.set_footer(text="You have 60 seconds to make selections.")
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

    @discord.ui.user_select(
        placeholder="Select members to deafen",
        min_values=0,
        max_values=25,
    )
    async def deafen_select_callback(self, select, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # Add logic and response

    @discord.ui.user_select(
        placeholder="Select members to undeafen",
        min_values=0,
        max_values=25,
    )
    async def undeafen_select_callback(self, select, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # Add logic and response
