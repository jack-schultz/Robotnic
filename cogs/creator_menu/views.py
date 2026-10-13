import logging
import discord
from discord.ui import View, Select, Button, Modal, InputText
from cogs.creator_menu.embeds import ListCreatorsEmbed, OptionsEmbed
from cogs.creator_menu.modals import EditModal
from config.i18n import t

logger = logging.getLogger(__name__)


class CreateView(View):
    def __init__(self, ctx, bot):
        super().__init__()
        self.bot = bot
        self.message = None
        self.author = ctx.author
        self.lang = bot.repos.guild_settings.get_language(ctx.guild.id)

        self.create_items(ctx.guild)

    def create_items(self, guild=None):
        # We require the guild id to get all creator channels for the guild
        # Either it's passed in or in self.update which has no inputs, we use the guild of the stored message
        # This doesn't work on first create as the view is made before the message attribute is updated after
        if not guild and self.message:
            guild = self.message.guild

        if guild is None:
            logger.error("No guild obj to create items for CreateView")
            return

        # Dropdown (own row)
        options = []
        creator_channel_ids = self.bot.repos.creator_channels.get_ids(guild_id=guild.id)
        for i, channel_id in enumerate(creator_channel_ids):
            channel = self.bot.get_channel(channel_id)
            if channel:
                options.append(discord.SelectOption(label=t("creator_menu.select.edit_option", self.lang, number=i+1, channel=channel.name), value=f"{channel.id}"))

        # If the dropdown has no options, add a placeholder one and disable it showing only the placeholder text
        is_disabled = False
        placeholder = t("creator_menu.select.placeholder", self.lang)
        if len(options) == 0:
            is_disabled = True
            options.append(discord.SelectOption(label="Option 1", value="1"),)
            placeholder = t("creator_menu.select.empty_placeholder", self.lang)

        select = Select(placeholder=placeholder, options=options, disabled=is_disabled)
        select.callback = self.select_callback
        if not is_disabled:  # Removes dropdown entirely instead of disabling
            self.add_item(select)

        # New Creator button
        creator_button = Button(label=t("creator_menu.button.new_creator", self.lang), style=discord.ButtonStyle.success)  # primary, danger
        creator_button.callback = self.creator_button_callback
        self.add_item(creator_button)

        options_button = Button(label=t("creator_menu.button.explain_options", self.lang), style=discord.ButtonStyle.primary)  # primary, danger
        options_button.callback = self.options_button_callback
        self.add_item(options_button)

    async def update(self):
        embeds = [
            ListCreatorsEmbed(self.message.guild, self.bot)
        ]
        self.clear_items()
        self.create_items()
        try:
            await self.message.edit(view=self, embeds=embeds)
        except discord.NotFound:
            logger.debug("CreateView message gone during update")

    # Dropdown callback
    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(t("common.not_your_menu", self.lang), ephemeral=True)

        modal = EditModal(self, creator_id=interaction.data["values"][0])
        try:
            await interaction.response.send_modal(modal)
        except discord.NotFound:
            guild_name = interaction.guild.name if interaction.guild else "unknown"
            logger.warning(
                f"Creator menu interaction expired before the edit modal could be sent in guild '{guild_name}'"
            )
            return None
        await self.update()  # If modal isn't submitted the dropdown won't be already used/selected
        return None

    # Button callback
    async def creator_button_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(t("common.not_your_menu", self.lang), ephemeral=True)

        new_creator_channel = await interaction.guild.create_voice_channel(t("creator_menu.new_creator.channel_name", self.lang))
        self.bot.repos.creator_channels.add(new_creator_channel.guild.id, new_creator_channel.id, t("creator_menu.new_creator.child_name", self.lang), 0, 0, 1, interaction.guild.default_role.id)

        embeds = [discord.Embed(), discord.Embed()]
        embeds[0].title = t("creator_menu.new_creator.created", self.lang, channel=new_creator_channel.mention)
        embeds[1].color = discord.Color.green()
        embeds[1].title = t("creator_menu.new_creator.best_results", self.lang)
        embeds[1].add_field(name="", value=t("creator_menu.new_creator.tip_move", self.lang), inline=True)
        embeds[1].add_field(name="", value=t("creator_menu.new_creator.tip_edit", self.lang), inline=True)
        embeds[1].footer = discord.EmbedFooter(t("common.disappear_seconds", self.lang, seconds=60))
        await interaction.response.send_message(f"", embeds=embeds, ephemeral=True, delete_after=60)
        await self.update()

        await self.bot.BotLogService.send(event="creator_create", message=t("bot_log.creator_created", guild=interaction.guild.name, user=interaction.user))
        return None

    async def options_button_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"", embed=OptionsEmbed(self.lang), ephemeral=True, delete_after=60)
        await self.update()
        return None

    async def on_timeout(self):
        if self.message is None:
            return
        try:
            await self.message.delete()
        except discord.NotFound:
            pass
        except Exception:
            logger.debug("Unable to delete CreateView message after timeout, message likely deleted already.")
