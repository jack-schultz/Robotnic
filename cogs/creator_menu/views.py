import logging
import discord
from discord.ui import View, Select, Button, Modal, InputText
from cogs.creator_menu.embeds import ListCreatorsEmbed, OptionsEmbed, CREATORS_PER_PAGE, get_creator_channels, page_count
from cogs.creator_menu.modals import EditModal
from config.i18n import t, fit_limit, OPTION_LIMIT

logger = logging.getLogger(__name__)


class CreateView(View):
    def __init__(self, ctx, bot):
        super().__init__()
        self.bot = bot
        self.message = None
        self.author = ctx.author
        self.guild = ctx.guild
        self.lang = bot.repos.guild_settings.get_language(ctx.guild.id)
        self.page = 0  # 0-based, clamped to the valid range on every render

    def render(self):
        """Rebuilds the components for the current page and returns the matching embeds."""
        creators = get_creator_channels(self.bot, self.guild)
        pages = page_count(len(creators))
        # Clamp in case creators were added/deleted since the last render (or the page was set past the end on purpose)
        self.page = min(max(self.page, 0), pages - 1)
        start = self.page * CREATORS_PER_PAGE
        numbered_creators = list(enumerate(creators, start=1))[start:start + CREATORS_PER_PAGE]

        self.clear_items()

        # Dropdown (row 0), only listing this page's creators. Left out entirely when there is nothing to edit
        if numbered_creators:
            options = [
                discord.SelectOption(
                    label=fit_limit(t("creator_menu.select.edit_option", self.lang, number=number, channel=channel.name), OPTION_LIMIT),
                    value=f"{channel.id}"
                )
                for number, channel in numbered_creators
            ]
            select = Select(placeholder=t("creator_menu.select.placeholder", self.lang), options=options, row=0)
            select.callback = self.select_callback
            self.add_item(select)

        # Page arrows (row 1), only when there is more than one page
        if pages > 1:
            prev_button = Button(emoji="◀", style=discord.ButtonStyle.secondary, disabled=self.page == 0, row=1)
            prev_button.callback = self.prev_page_callback
            self.add_item(prev_button)

            next_button = Button(emoji="▶", style=discord.ButtonStyle.secondary, disabled=self.page >= pages - 1, row=1)
            next_button.callback = self.next_page_callback
            self.add_item(next_button)

        # New Creator button (row 2)
        creator_button = Button(label=t("creator_menu.button.new_creator", self.lang), style=discord.ButtonStyle.success, row=2)  # primary, danger
        creator_button.callback = self.creator_button_callback
        self.add_item(creator_button)

        options_button = Button(label=t("creator_menu.button.explain_options", self.lang), style=discord.ButtonStyle.primary, row=2)  # primary, danger
        options_button.callback = self.options_button_callback
        self.add_item(options_button)

        return [ListCreatorsEmbed(self.bot, self.guild, numbered_creators, self.page, pages)]

    async def update(self, interaction: discord.Interaction = None):
        """Re-renders the menu. Pass the interaction when it hasn't been responded to yet so the edit answers it."""
        embeds = self.render()
        try:
            if interaction is not None:
                await interaction.response.edit_message(view=self, embeds=embeds)
            else:
                await self.message.edit(view=self, embeds=embeds)
        except discord.NotFound:
            logger.debug("CreateView message gone during update")

    # Page arrow callbacks
    async def prev_page_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(t("common.not_your_menu", self.lang), ephemeral=True)
        self.page -= 1
        await self.update(interaction)
        return None

    async def next_page_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(t("common.not_your_menu", self.lang), ephemeral=True)
        self.page += 1
        await self.update(interaction)
        return None

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
        self.page = page_count(len(get_creator_channels(self.bot, self.guild))) - 1  # Jump to the last page so the new creator is visible
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
