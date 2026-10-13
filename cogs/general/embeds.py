import discord
from config.i18n import t, command_text


class DonateEmbed(discord.Embed):
    def __init__(self, lang):
        super().__init__()
        self.color = discord.Color.green()
        self.title = t("general.donate.title", lang)
        self.description = t("general.donate.description", lang)
        self.add_field(
            name=t("general.donate.kofi", lang),
            value="",
            inline=False
        )


class HelpEmbed(discord.Embed):
    def __init__(self, lang):
        super().__init__()
        self.color = discord.Color.green()
        self.title = t("general.help.title", lang)
        self.description = (
        )
        self.add_field(
            name=command_text("commands.setup", language=lang),
            value=t("general.help.setup", lang),
            inline=True
        )
        self.add_field(
            name=command_text("commands.settings", "commands.settings.controls", language=lang),
            value=t("general.help.settings_controls", lang),
            inline=True
        )
        self.add_field(
            name=command_text("commands.settings", "commands.settings.logging", language=lang),
            value=t("general.help.settings_logging", lang),
            inline=True
        )
        self.add_field(
            name=command_text("commands.settings", "commands.settings.profanity_filter", language=lang),
            value=t("general.help.settings_profanity_filter", lang),
            inline=True
        )
        self.add_field(
            name=command_text("commands.settings", "commands.settings.owner", "commands.settings.owner.dm_on_create", language=lang),
            value=t("general.help.settings_dm_owner", lang),
            inline=True
        )
        self.add_field(
            name=command_text("commands.settings", "commands.settings.language", language=lang),
            value=t("general.help.settings_language", lang),
            inline=True
        )
        self.add_field(
            name=command_text("commands.settings", "commands.settings.placeholder", "commands.settings.placeholder.add", language=lang),
            value=t("general.help.settings_placeholder_add", lang),
            inline=True
        )
        self.add_field(
            name=command_text("commands.settings", "commands.settings.placeholder", "commands.settings.placeholder.list", language=lang),
            value=t("general.help.settings_placeholder_list", lang),
            inline=True
        )
        self.add_field(
            name=command_text("commands.settings", "commands.settings.placeholder", "commands.settings.placeholder.remove", language=lang),
            value=t("general.help.settings_placeholder_remove", lang),
            inline=True
        )
        self.add_field(
            name=" | ".join(command_text(key, language=lang) for key in ("commands.donate", "commands.support", "commands.website")),
            value=t("general.help.donate", lang),
            inline=True
        )
        self.set_footer(text=t("general.help.footer", lang))
