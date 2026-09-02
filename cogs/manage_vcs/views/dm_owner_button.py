import discord


class AcknowledgeButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="I Understand",
        style=discord.ButtonStyle.success,
        custom_id="dm_owner_acknowledge",
    )
    async def acknowledge(self, button: discord.ui.Button, interaction: discord.Interaction):
        interaction.client.repos.user_notifications.set_dm_owner_controls(interaction.user.id)
        button.disabled = True
        await interaction.response.edit_message(view=self)
