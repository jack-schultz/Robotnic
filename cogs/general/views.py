import discord


class ButtonsView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.create_items()

    def create_items(self):
        self.add_item(
            discord.ui.Button(
                label="Ko-fi",
                url="https://ko-fi.com/jackschultzdev",
                emoji="💖",
                style=discord.ButtonStyle.link
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Support Server",
                url="https://discord.gg/rcAREJyMV5",
                emoji="🔧",
                style=discord.ButtonStyle.link
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Website",
                url="https://jackschultz.dev/Robotnic/",
                emoji="🌏",
                style=discord.ButtonStyle.link
            )
        )
