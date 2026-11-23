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
    def __init__(self, lang, user_lang):
        super().__init__()
        self.color = discord.Color.green()
        self.title = t("general.help.title", user_lang)
        self.description = (
        )
        self.add_field(
            name=command_text("commands.setup", language=user_lang),
            value=t("general.help.setup", user_lang),
            inline=True
        )
        self.add_field(
            name=command_text("commands.settings", "commands.settings.controls", language=user_lang),
            value=t("general.help.settings_controls", user_lang),
            inline=True
        )
        self.add_field(
            name=command_text("commands.settings", "commands.settings.logging", language=user_lang),
            value=t("general.help.settings_logging", user_lang),
            inline=True
        )
        self.add_field(
            name=command_text("commands.settings", "commands.settings.profanity_filter", language=user_lang),
            value=t("general.help.settings_profanity_filter", user_lang),
            inline=True
        )
        self.add_field(
            name=command_text("commands.settings", "commands.settings.owner", "commands.settings.owner.dm_on_create", language=user_lang),
            value=t("general.help.settings_dm_owner", user_lang),
            inline=True
        )
        self.add_field(
            name=command_text("commands.settings", "commands.settings.language", language=user_lang),
            value=t("general.help.settings_language", user_lang),
            inline=True
        )
        self.add_field(
            name=command_text("commands.settings", "commands.settings.placeholder", "commands.settings.placeholder.add", language=user_lang),
            value=t("general.help.settings_placeholder_add", user_lang),
            inline=True
        )
        self.add_field(
            name=command_text("commands.settings", "commands.settings.placeholder", "commands.settings.placeholder.list", language=user_lang),
            value=t("general.help.settings_placeholder_list", user_lang),
            inline=True
        )
        self.add_field(
            name=command_text("commands.settings", "commands.settings.placeholder", "commands.settings.placeholder.remove", language=user_lang),
            value=t("general.help.settings_placeholder_remove", user_lang),
            inline=True
        )
        self.add_field(
            name=" | ".join(command_text(key, language=user_lang) for key in ("commands.donate", "commands.support", "commands.website")),
            value=t("general.help.donate", user_lang),
            inline=True
        )
        self.set_footer(text=t("general.help.footer", user_lang))
