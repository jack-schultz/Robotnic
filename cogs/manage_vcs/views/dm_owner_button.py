import discord


LABEL = "Don’t DM me about channel controls again"
NEXT_LABEL = "Acknowledged"
UNDO = "Undo?"

ACKNOWLEDGE_CUSTOM_ID = "dm_owner_acknowledge"
ACKNOWLEDGED_CUSTOM_ID = "dm_owner_acknowledged"
UNDO_CUSTOM_ID = "dm_owner_acknowledge_undo"
JUMP_CUSTOM_ID = "dm_jump_link"


# jump_link is passed from view to view while bot is online
# Once view turns persistent, the jump_link is lost and is no longer displayed
class AcknowledgeButtonView(discord.ui.View):
    """Initial state: only the acknowledge button is visible."""

    def __init__(self, jump_link=None):
        super().__init__(timeout=None)

        self.jump_link = jump_link
        if jump_link:
            self.jump_link_button = discord.ui.Button(
                label="Control Panel",
                url=f"{jump_link}",
                emoji="⚙️",
                style=discord.ButtonStyle.link,
            )
            self.add_item(self.jump_link_button)

        self.acknowledge_button = discord.ui.Button(
            label=LABEL,
            style=discord.ButtonStyle.primary,
            custom_id=ACKNOWLEDGE_CUSTOM_ID,
            row=2
        )

        self.acknowledge_button.callback = self.acknowledge

        self.add_item(self.acknowledge_button)

    async def acknowledge(self, interaction: discord.Interaction):
        interaction.client.repos.user_notifications.set_dm_owner_controls(
            interaction.user.id
        )

        await interaction.response.edit_message(
            view=AcknowledgedButtonView(self.jump_link)
        )


class AcknowledgedButtonView(discord.ui.View):
    """Acknowledged state: disabled acknowledge button + Undo."""

    def __init__(self, jump_link=None):
        super().__init__(timeout=None)

        self.jump_link = jump_link
        if jump_link:
            self.jump_link_button = discord.ui.Button(
                label="Control Panel",
                url=f"{jump_link}",
                emoji="↗️",
                style=discord.ButtonStyle.link,
            )
            self.add_item(self.jump_link_button)

        self.acknowledged_button = discord.ui.Button(
            label=NEXT_LABEL,
            style=discord.ButtonStyle.success,
            custom_id=ACKNOWLEDGED_CUSTOM_ID,
            disabled=True,
            row=2
        )

        self.undo_button = discord.ui.Button(
            label=UNDO,
            style=discord.ButtonStyle.secondary,
            custom_id=UNDO_CUSTOM_ID,
            row=2
        )

        self.undo_button.callback = self.undo

        self.add_item(self.acknowledged_button)
        self.add_item(self.undo_button)

    async def undo(self, interaction: discord.Interaction):
        interaction.client.repos.user_notifications.clear_dm_owner_controls(
            interaction.user.id
        )

        await interaction.response.edit_message(
            view=AcknowledgeButtonView(self.jump_link)
        )