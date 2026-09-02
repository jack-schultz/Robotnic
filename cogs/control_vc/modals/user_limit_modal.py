import discord
from cogs.control_vc.embed_scheduler import schedule_info_embed


class UserLimitModal(discord.ui.Modal):
    def __init__(self, bot, channel):
        super().__init__(title="Edit Your Channel")
        self.bot = bot
        self.channel = channel

        # Define the text inputs
        self.user_limit = discord.ui.InputText(
            label="User Limit (Unlimited = 0)",
            placeholder=f"{channel.user_limit}",
            required=False,
            max_length=2
        )

        self.add_item(self.user_limit)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user_limit = self.user_limit.value or str(self.channel.user_limit)

        if not user_limit.isnumeric():
            embed = discord.Embed(
                title="Invalid Input",
                description="User limit must be a number.",
                color=discord.Color.red()
            )
            embed.set_footer(text="This message will disappear in 15 seconds.")
            try:
                await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
            except (discord.NotFound, discord.HTTPException):
                pass
            return

        limit_value = int(user_limit)
        if limit_value != self.channel.user_limit:
            try:
                await self.channel.edit(user_limit=limit_value)
            except discord.NotFound:
                return

            await schedule_info_embed(self.bot, self.channel, user_limit=user_limit)

        embed = discord.Embed(
            title="Changes Saved",
            description=f"Channel limit changed to {user_limit}",
            color=discord.Color.blue()
        )
        embed.set_footer(text="This message will disappear in 15 seconds.")
        try:
            await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
        except (discord.NotFound, discord.HTTPException):
            pass
