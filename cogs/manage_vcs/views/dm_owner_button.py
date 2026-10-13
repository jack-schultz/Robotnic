import discord
from config.i18n import t


ACKNOWLEDGE_CUSTOM_ID = "dm_owner_acknowledge"
ACKNOWLEDGED_CUSTOM_ID = "dm_owner_acknowledged"
UNDO_CUSTOM_ID = "dm_owner_acknowledge_undo"
JUMP_CUSTOM_ID = "dm_jump_link"


# jump_link and lang are passed from view to view while bot is online
# Once view turns persistent, the jump_link is lost and is no longer displayed, and lang falls back to the default
class AcknowledgeButtonView(discord.ui.View):
    """Initial state: only the acknowledge button is visible."""

    def __init__(self, jump_link=None, lang=None):
        super().__init__(timeout=None)

        self.jump_link = jump_link
        self.lang = lang
        if jump_link:
            self.jump_link_button = discord.ui.Button(
                label=t("owner.dm.control_panel", lang),
                url=f"{jump_link}",
                emoji="⚙️",
                style=discord.ButtonStyle.link,
            )
            self.add_item(self.jump_link_button)

        self.acknowledge_button = discord.ui.Button(
            label=t("owner.dm.acknowledge", lang),
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
            view=AcknowledgedButtonView(self.jump_link, self.lang)
        )


class AcknowledgedButtonView(discord.ui.View):
    """Acknowledged state: disabled acknowledge button + Undo."""

    def __init__(self, jump_link=None, lang=None):
        super().__init__(timeout=None)

        self.jump_link = jump_link
        self.lang = lang
        if jump_link:
            self.jump_link_button = discord.ui.Button(
                label=t("owner.dm.control_panel", lang),
                url=f"{jump_link}",
                emoji="⚙️",
                style=discord.ButtonStyle.link,
            )
            self.add_item(self.jump_link_button)

        self.acknowledged_button = discord.ui.Button(
            label=t("owner.dm.acknowledged", lang),
            style=discord.ButtonStyle.success,
            custom_id=ACKNOWLEDGED_CUSTOM_ID,
            disabled=True,
            row=2
        )

        self.undo_button = discord.ui.Button(
            label=t("owner.dm.undo", lang),
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
            view=AcknowledgeButtonView(self.jump_link, self.lang)
        )
