import discord
from config.i18n import t


class ButtonsView(discord.ui.View):
    def __init__(self, lang):
        super().__init__()
        self.create_items(lang)

    def create_items(self, lang):
        self.add_item(
            discord.ui.Button(
                label=t("general.button.kofi", lang),
                url="https://ko-fi.com/jackschultzdev",
                emoji="💖",
                style=discord.ButtonStyle.link
            )
        )
        self.add_item(
            discord.ui.Button(
                label=t("general.button.support_server", lang),
                url="https://discord.gg/rcAREJyMV5",
                emoji="🔧",
                style=discord.ButtonStyle.link
            )
        )
        self.add_item(
            discord.ui.Button(
                label=t("general.button.website", lang),
                url="https://jackschultz.dev/Robotnic/",
                emoji="🌏",
                style=discord.ButtonStyle.link
            )
        )
