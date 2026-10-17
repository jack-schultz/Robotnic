import discord
from discord.ui import View, Select, Button, Modal, InputText
from config.i18n import t, fit_limit, MODAL_TITLE_LIMIT, LABEL_LIMIT, SELECT_PLACEHOLDER_LIMIT, OPTION_LIMIT


def format_list(items, lang):
    items = [f"`{str(i).capitalize()}`" for i in items]
    if not items:
        return t("common.list.none", lang)
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return t("common.list.two", lang, first=items[0], second=items[1])
    return t("common.list.many", lang, items=t("common.list.separator", lang).join(items[:-1]), last=items[-1])


class ControlsModal(discord.ui.DesignerModal):
    def __init__(self, bot, ctx):
        self.lang = bot.repos.guild_settings.get_language(ctx.guild.id)
        super().__init__(title=fit_limit(t("settings.modal.title", self.lang), MODAL_TITLE_LIMIT))
        self.bot = bot
        guild_settings = self.bot.repos.guild_settings.get(ctx.guild.id)

        self._add_enabled_controls(guild_settings)
        self._add_mention_owner(guild_settings)
        self._add_control_options(guild_settings)

    def _add_enabled_controls(self, guild_settings):
        enabled_controls = guild_settings["enabled_controls"]
        controls = [
            ("rename", "🏷️"),
            ("limit", "🚧"),
            ("clear", "🧽"),
            ("ban", "🔨"),
            ("mute", "🔇"),
            ("deafen", "🔕"),
            ("give", "🎁"),
            ("delete", "🗑️"),
            ("lock", "🔒"),
            ("hide", "🙈"),
        ]
        controls_options = [
            discord.SelectOption(value=control, label=fit_limit(t(f"settings.controls.{control}", self.lang), OPTION_LIMIT), emoji=emoji, default=control in enabled_controls)
            for control, emoji in controls
        ]
        controls_select = Select(placeholder=fit_limit(t("settings.controls.select_placeholder", self.lang), SELECT_PLACEHOLDER_LIMIT), options=controls_options, max_values=len(controls_options), min_values=0, required=False)
        self.controls_select_label = discord.ui.Label(
            fit_limit(t("settings.controls.select_label", self.lang), LABEL_LIMIT),
            controls_select,
        )
        self.add_item(self.controls_select_label)

    def _save_enabled_controls(self, guild_id, embed):
        enabled_controls = self.controls_select_label.item.values
        self.bot.repos.guild_settings.edit(guild_id, enabled_controls=list(enabled_controls))
        embed.add_field(name=t("settings.controls.enabled_field", self.lang), value=f"{format_list(enabled_controls, self.lang)}", inline=False)

    def _add_mention_owner(self, guild_settings):
        mention_owner = guild_settings["mention_owner_bool"]
        options = [
            discord.SelectOption(value="true", label=fit_limit(t("settings.controls.mention_yes", self.lang), OPTION_LIMIT), default=mention_owner),
            discord.SelectOption(value="false", label=fit_limit(t("settings.controls.mention_no", self.lang), OPTION_LIMIT), default=not mention_owner),
        ]

        self.mention_owner_label = discord.ui.Label(
            fit_limit(t("settings.controls.mention_label", self.lang), LABEL_LIMIT),
            discord.ui.Select(
                options=options,
                min_values=1,
                max_values=1,
                required=True
            ),
        )
        self.add_item(self.mention_owner_label)

    def _save_mention_owner(self, guild_id, embed):
        should_mention = self.mention_owner_label.item.values[0]
        if should_mention == "false":
            should_mention = False
        self.bot.repos.guild_settings.edit(guild_id, mention_owner=should_mention)
        embed.add_field(name=t("settings.controls.mention_field", self.lang), value=f"`{should_mention}`", inline=False)

    def _add_control_options(self, guild_settings):
        enabled_options = guild_settings["control_options"]
        default = "dropdown"
        if "dropdown" in enabled_options:
            default = "dropdown"
        elif "buttons" in enabled_options and "labels" in enabled_options:
            default = "buttons_labels"
        elif "buttons" in enabled_options:
            default = "buttons_icons"
        control_options = [
            discord.SelectOption(value=control_type, label=fit_limit(t(f"settings.controls.type_{control_type}", self.lang), OPTION_LIMIT), default=default == control_type)
            for control_type in ("dropdown", "buttons_labels", "buttons_icons")
        ]
        options_select = Select(placeholder=fit_limit(t("settings.controls.type_placeholder", self.lang), SELECT_PLACEHOLDER_LIMIT), options=control_options, max_values=1, min_values=1, required=True)
        self.options_select_label = discord.ui.Label(
            fit_limit(t("settings.controls.type_label", self.lang), LABEL_LIMIT),
            options_select,
        )
        self.add_item(self.options_select_label)

    def _save_control_options(self, guild_id, embed):
        control_type = self.options_select_label.item.values[0]
        selected_control_options = []

        # Control type
        control_type_map = {
            "dropdown": {"dropdown", "labels"},
            "buttons_labels": {"buttons", "icons", "labels"},
            "buttons_icons": {"buttons", "icons"},
        }
        selected_control_options.extend(control_type_map.get(control_type, []))

        self.bot.repos.guild_settings.edit(guild_id, control_options=selected_control_options)
        embed.add_field(name=t("settings.controls.type_field", self.lang), value=f"`{t(f'settings.controls.type_{control_type}', self.lang)}`", inline=False)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=t("settings.modal.submitted", self.lang),
            description=f"",
            color=discord.Color.green()
        )
        embed.set_footer(text=t("common.disappear_seconds", self.lang, seconds=60))

        self._save_enabled_controls(interaction.guild_id, embed)
        self._save_mention_owner(interaction.guild_id, embed)
        self._save_control_options(interaction.guild_id, embed)

        await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=60)


class LogsModal(discord.ui.DesignerModal):
    def __init__(self, bot, ctx):
        self.lang = bot.repos.guild_settings.get_language(ctx.guild.id)
        super().__init__(title=fit_limit(t("settings.modal.title", self.lang), MODAL_TITLE_LIMIT))
        self.bot = bot
        guild_settings = self.bot.repos.guild_settings.get(ctx.guild.id)

        self._add_log_channel(guild_settings)
        self._add_log_events(guild_settings)

    def _add_log_channel(self, guild_settings):
        if guild_settings["logs_channel_id"] is not None and int(guild_settings["logs_channel_id"]) != 0:
            log_channel = self.bot.get_channel(guild_settings["logs_channel_id"])
        else:
            log_channel = None

        self.log_channel_select = discord.ui.Label(
            fit_limit(t("settings.logs.channel_label", self.lang), LABEL_LIMIT),
            discord.ui.ChannelSelect(
                channel_types=[discord.ChannelType.text],
                min_values=1,
                max_values=1,
                default_values=[log_channel] if log_channel else None,
                required=False
            ),
        )
        self.add_item(self.log_channel_select)

    def _save_log_channel(self, guild_id, embed):
        if len(self.log_channel_select.item.values) >= 1:
            log_channel = self.log_channel_select.item.values[0]
            self.bot.repos.guild_settings.edit(guild_id, logs_channel_id=log_channel.id)
            embed.add_field(name=t("settings.logs.channel_field", self.lang), value=f"{log_channel.mention}/`#{log_channel.name}` (`{log_channel.id}`)", inline=False)
        else:
            self.bot.repos.guild_settings.edit(guild_id, logs_channel_id=0)
            embed.add_field(name=t("settings.logs.channel_field", self.lang), value=t("settings.logs.channel_disabled", self.lang), inline=False)

    def _add_log_events(self, guild_settings):
        enabled_events = guild_settings["enabled_log_events"]
        events = [
            ("channel_create", "🎁"),
            ("channel_rename", "🏷️"),
            ("channel_remove", "🗑️"),
            ("profanity_block", "😶"),
        ]
        events_options = [
            discord.SelectOption(value=event, label=fit_limit(t(f"settings.logs.event.{event}", self.lang), OPTION_LIMIT), emoji=emoji, default=event in enabled_events)
            for event, emoji in events
        ]
        events_select = Select(placeholder=fit_limit(t("settings.logs.events_placeholder", self.lang), SELECT_PLACEHOLDER_LIMIT), options=events_options, max_values=len(events_options), min_values=0, required=False)

        self.events_select_label = discord.ui.Label(
            fit_limit(t("settings.logs.events_label", self.lang), LABEL_LIMIT),
            events_select,
        )
        self.add_item(self.events_select_label)

    def _save_log_events(self, guild_id, embed):
        enabled_log_events = self.events_select_label.item.values
        self.bot.repos.guild_settings.edit(guild_id, enabled_log_events=enabled_log_events)
        embed.add_field(name=t("settings.logs.events_field", self.lang), value=f"{format_list(enabled_log_events, self.lang)}", inline=False)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=t("settings.modal.submitted", self.lang),
            description=f"",
            color=discord.Color.green()
        )
        embed.set_footer(text=t("common.disappear_seconds", self.lang, seconds=60))

        self._save_log_channel(interaction.guild_id, embed)
        self._save_log_events(interaction.guild_id, embed)

        await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=60)
