import discord

BAN_PERMS = {
    "connect": False,
    "view_channel": False,
}

ALLOW_PERMS = {
    "connect": True,
    "view_channel": True,
}


# Abstracted into functions allowing both the control menu or context menu (right click menu) to use the same ban/allow logic
# 1. List of users is fed into ban_targets() or allow_targets()
# 2. ban_targets() or allow_targets() filters targets and passes them to _apply_overwrites()
# 3. _apply_overwrites() adds them to current overwrites, updates the channel and returns affected
# 4. ban_targets() uses effected list to disconnect users
# 5. ban_targets() or allow_targets() return affected list

async def _apply_overwrites(channel, targets, perms):
    affected = []
    overwrites = channel.overwrites
    overwrite = discord.PermissionOverwrite(**perms)

    for target in targets:
        if not target:
            continue
        overwrites[target] = overwrite
        affected.append(target)

    if affected:
        await channel.edit(overwrites=overwrites)

    return affected


async def ban_targets(bot, channel, targets):
    owner_id = bot.repos.temp_channels.get_info(channel.id).owner_id
    connected_members = channel.members
    valid_targets = []

    for target in targets:
        if not target:
            continue
        if isinstance(target, discord.Member) and target.id == owner_id:
            continue
        if isinstance(target, discord.Member) and target.id == bot.user.id:
            continue
        valid_targets.append(target)

    affected = await _apply_overwrites(channel, valid_targets, BAN_PERMS)

    for target in affected:
        if isinstance(target, discord.Member) and target in connected_members:
            await target.move_to(None)

    return affected


async def allow_targets(bot, channel, targets):
    return await _apply_overwrites(channel, targets, ALLOW_PERMS)


class BanUserView(discord.ui.View):
    def __init__(self, bot, channel):
        super().__init__(timeout=300)
        self.bot = bot
        self.channel = channel
        self.message = None

    @discord.ui.mentionable_select(
        placeholder="Select members or roles to ban",
        min_values=0,
        max_values=25
    )
    async def ban_select_callback(self, select, interaction: discord.Interaction):
        affected = await ban_targets(self.bot, self.channel, select.values)

        if affected:
            embed = discord.Embed(
                title="Banned!",
                description=f"Banned {len(affected)} member(s)/role(s) from your channel.",
                color=0x00FF00
            )
            embed.set_footer(text="This message will disappear in 10 seconds.")
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
                delete_after=10
            )
        else:
            embed = discord.Embed(
                title="Select valid users or roles to ban",
                description=f"",
                color=0x00FF00
            )
            embed.set_footer(text="This message will disappear in 10 seconds.")
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
                delete_after=10
            )

    # ---- ALLOW SELECT ----
    @discord.ui.mentionable_select(
        placeholder="Select members or roles to allow",
        min_values=0,
        max_values=25
    )
    async def allow_select_callback(self, select, interaction: discord.Interaction):
        affected = await allow_targets(self.bot, self.channel, select.values)

        if affected:
            embed = discord.Embed(
                title="Allowed!",
                description=f"Allowed {len(affected)} member(s)/role(s) in your channel.",
                color=0x00FF00
            )
            embed.set_footer(text="This message will disappear in 10 seconds.")
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
                delete_after=10
            )
        else:
            embed = discord.Embed(
                title="Select valid users or roles to Allow",
                description=f"",
                color=0x00FF00
            )
            embed.set_footer(text="This message will disappear in 10 seconds.")
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
                delete_after=10
            )

    async def send_initial_message(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔨 Manage access to your channel",
            description=(
                "Use the menus below to ban or allow members/roles.\n"
                "Banned users cannot view or connect to the channel."
            ),
            color=0x00FF00
        )
        embed.set_footer(text="You have 60 seconds to make selections.")

        self.message = await interaction.followup.send(
            embed=embed,
            view=self,
            ephemeral=True,
            wait=True
        )

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except discord.NotFound:
                pass
