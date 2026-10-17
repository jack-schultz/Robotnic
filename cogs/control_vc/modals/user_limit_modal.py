import discord
from config.i18n import t, fit_limit, MODAL_TITLE_LIMIT, LABEL_LIMIT, PLACEHOLDER_LIMIT


class UserLimitModal(discord.ui.Modal):
    def __init__(self, bot, channel):
        self.lang = bot.repos.guild_settings.get_language(channel.guild.id)
        super().__init__(title=fit_limit(t("control.limit.modal_title", self.lang), MODAL_TITLE_LIMIT))
        self.bot = bot
        self.channel = channel

        # Define the text inputs
        self.user_limit = discord.ui.InputText(
            label=fit_limit(t("control.limit.label", self.lang), LABEL_LIMIT),
            placeholder=fit_limit(f"{channel.user_limit}", PLACEHOLDER_LIMIT),
            required=False,
            max_length=2
        )

        self.add_item(self.user_limit)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user_limit = self.user_limit.value or str(self.channel.user_limit)

        if not user_limit.isnumeric():
            embed = discord.Embed(
                title=t("control.limit.invalid_title", self.lang),
                description=t("control.limit.invalid_description", self.lang),
                color=discord.Color.red()
            )
            embed.set_footer(text=t("common.disappear_seconds", self.lang, seconds=15))
            try:
                reply = await interaction.followup.send(embed=embed, ephemeral=True, wait=True)
                await reply.delete(delay=15)
            except (discord.NotFound, discord.HTTPException):
                pass
            return

        limit_value = int(user_limit)
        if limit_value != self.channel.user_limit:
            try:
                await self.channel.edit(user_limit=limit_value)
            except discord.NotFound:
                return

            await self.bot.EmbedUpdateScheduler.schedule(self.channel, user_limit=user_limit)

        embed = discord.Embed(
            title=t("common.changes_saved", self.lang),
            description=t("control.limit.saved_description", self.lang, limit=user_limit),
            color=discord.Color.blue()
        )
        embed.set_footer(text=t("common.disappear_seconds", self.lang, seconds=15))
        try:
            reply = await interaction.followup.send(embed=embed, ephemeral=True, wait=True)
            await reply.delete(delay=15)
        except (discord.NotFound, discord.HTTPException):
            pass
