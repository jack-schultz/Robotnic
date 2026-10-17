import discord
from config.i18n import t, fit_limit, MODAL_TITLE_LIMIT, LABEL_LIMIT, PLACEHOLDER_LIMIT, SELECT_PLACEHOLDER_LIMIT


class PlaceholderAddModal(discord.ui.DesignerModal):
    def __init__(self, bot, ctx):
        self.lang = bot.repos.guild_settings.get_language(ctx.guild.id)
        super().__init__(title=fit_limit(t("settings.placeholder.modal_title", self.lang), MODAL_TITLE_LIMIT))
        self.bot = bot

        self.placeholder_label = discord.ui.Label(
            fit_limit(t("settings.placeholder.placeholder_label", self.lang), LABEL_LIMIT),
            discord.ui.TextInput(
                placeholder=fit_limit(t("settings.placeholder.placeholder_example", self.lang), PLACEHOLDER_LIMIT),
                required=True,
                max_length=100,
            ),
        )
        self.add_item(self.placeholder_label)

        self.replace_text_label = discord.ui.Label(
            fit_limit(t("settings.placeholder.replace_label", self.lang), LABEL_LIMIT),
            discord.ui.TextInput(
                placeholder=fit_limit(t("settings.placeholder.replace_placeholder", self.lang), PLACEHOLDER_LIMIT),
                required=True,
                max_length=100,
            ),
        )
        self.add_item(self.replace_text_label)

        self.role_required_label = discord.ui.Label(
            fit_limit(t("settings.placeholder.role_label", self.lang), LABEL_LIMIT),
            discord.ui.RoleSelect(
                min_values=1,
                max_values=1,
                required=True,
                placeholder=fit_limit(t("settings.placeholder.role_placeholder", self.lang), SELECT_PLACEHOLDER_LIMIT),
            ),
        )
        self.add_item(self.role_required_label)

    async def callback(self, interaction: discord.Interaction):
        placeholder = self.placeholder_label.item.value.strip()
        replace_text = self.replace_text_label.item.value
        role = self.role_required_label.item.values[0] if self.role_required_label.item.values else None

        self.bot.repos.placeholders.add(
            guild_id=interaction.guild.id,
            placeholder=placeholder,
            replace_text=replace_text,
            role_id=role.id if role else None,
        )

        embed = discord.Embed(
            title=t("settings.placeholder.added", self.lang),
            description="",
            color=discord.Color.green(),
        )
        embed.add_field(name=t("settings.placeholder.placeholder_label", self.lang), value=f"`{placeholder}`", inline=False)
        embed.add_field(name=t("settings.placeholder.replace_label", self.lang), value=f"`{replace_text}`", inline=False)
        embed.add_field(
            name=t("settings.placeholder.role_label", self.lang),
            value=role.mention if role else t("common.none_code", self.lang),
            inline=False,
        )
        embed.set_footer(text=t("common.disappear_seconds", self.lang, seconds=60))

        await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=60)
