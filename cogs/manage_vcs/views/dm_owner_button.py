import discord


class AcknowledgeButtonView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="I Understand",
        style=discord.ButtonStyle.success,
        custom_id="dm_owner_acknowledge",
    )
    async def acknowledge(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bot.repos.user_notifications.set_dm_owner_controls(interaction.user.id)
        button.disabled = True
        await interaction.response.edit_message(view=self)
