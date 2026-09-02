import discord


class AcknowledgeButtonView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__()
        self.create_items(user_id)

    def create_items(self, user_id):
        self.add_item(
            discord.ui.Button(
                label="I Understand",
                emoji="",
                style=discord.ButtonStyle.success,
                custom_id=f"understand_{user_id}",
            )
        )
