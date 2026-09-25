import discord
from discord import Role
from discord.ext import commands
from cogs.settings.modals import ControlsModal, LogsModal
from cogs.settings.placeholders.modals import PlaceholderAddModal


async def placeholder_remove_autocomplete(ctx: discord.AutocompleteContext):
    entries = ctx.bot.repos.placeholders.get_all(ctx.interaction.guild.id)
    query = (ctx.value or "").lower()
    choices = []
    for entry in entries:
        label = f"'{entry['placeholder']}' → '{entry['replace_text']}' for role: '{ctx.interaction.guild.get_role(entry['role_id']).name}'"
        if query and query not in label.lower():
            continue
        choices.append(discord.OptionChoice(name=label[:100], value=str(entry["id"])))
        if len(choices) >= 25:
            break
    return choices


class SettingsMenuCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    settings = discord.SlashCommandGroup(
        "settings",
        "Change Guild Settings",
        default_member_permissions=discord.Permissions(manage_channels=True),
    )

    @settings.command(description="Select which controls users should have access to by default")
    async def logging(
            self,
            ctx: discord.ApplicationContext,
    ):
        await ctx.send_modal(LogsModal(self.bot, ctx))

        embed = discord.Embed(
            title="",
            description=f"Make sure to click \"SUBMIT\" after editing the pop-up menu.",
            color=discord.Color.yellow()
        )
        embed.set_footer(text="This message will disappear in 30 seconds.")
        reply = await ctx.send_followup(embed=embed, ephemeral=True, wait=True)
        await reply.delete(delay=30)

    @settings.command(description="Select which controls users should have access to by default")
    async def controls(
        self,
        ctx: discord.ApplicationContext,
    ):
        await ctx.send_modal(ControlsModal(self.bot, ctx))

        embed = discord.Embed(
            title="",
            description=f"Make sure to click \"SUBMIT\" after editing the pop-up menu.",
            color=discord.Color.yellow()
        )
        embed.set_footer(text="This message will disappear in 30 seconds.")
        reply = await ctx.send_followup(embed=embed, ephemeral=True, wait=True)
        await reply.delete(delay=30)

    @settings.command(description="Set the profanity check in channel names")
    async def profanity_filter(
        self,
        ctx: discord.ApplicationContext,
        mode: discord.Option(
            str,
            choices=["off", "alert", "alert & block"],
            description="Filter mode, alert will send a profanity alert in the logs channel."
        )
    ):
        self.bot.repos.guild_settings.edit(ctx.guild_id, profanity_filter=mode)
        await ctx.respond(
            f"profanity filter set to `{mode}`"
        )

    owner = settings.create_subgroup(
        "owner",
        "Manage temp channel owner related settings",
    )

    @owner.command(name="dm-on-create", description="Enable or disable DMing channel owners on create")
    async def dm_owner(
        self,
        ctx: discord.ApplicationContext,
        enabled: discord.Option(
            bool,
            description="Whether to DM owners when they create a channel",
        ),
    ):
        self.bot.repos.guild_settings.edit(ctx.guild_id, dm_owner=enabled)
        await ctx.respond(f"dm-owner set to `{enabled}`")

    @owner.command(name="role-set", description="Set a role given to owners of a Temp Channel")
    async def role_set(
        self,
        ctx: discord.ApplicationContext,
        owner_role: discord.Option(
            discord.Role,
            description="Role given to VC Owners",
        ),
    ):
        self.bot.repos.guild_settings.edit(ctx.guild_id, owner_role_id=owner_role.id)
        await ctx.respond(f"Owner role set to `{owner_role.name} ({owner_role.id})`")

    @owner.command(name="role-clear", description="Set a role given to owners of a Temp Channel")
    async def role_clear(
        self,
        ctx: discord.ApplicationContext,
    ):
        self.bot.repos.guild_settings.edit(ctx.guild_id, owner_role_id=0)
        await ctx.respond(f"Owner role has been cleared.")

    @owner.command(name="role-get", description="Get the currently selected role given to owners of Temp Channels")
    async def role_get(
        self,
        ctx: discord.ApplicationContext
    ):
        settings = self.bot.repos.guild_settings.get(ctx.guild_id)
        if settings is None:
            await ctx.respond(f"Owner role could not be retrieved.")
            return

        owner_role_id = settings["owner_role_id"]
        if owner_role_id is None or owner_role_id == 0:
            await ctx.respond(f"Owner role is not set.")
            return

        owner_role = ctx.guild.get_role(owner_role_id)
        if owner_role is None:
            await ctx.respond(f"Owner role could not be retrieved.")
            return

        await ctx.respond(f"Owner role set to `{owner_role.name} ({owner_role.id})`")

    @owner.command(name="prefix-set", description="Set a prefix given to owners of a Temp Channel")
    async def role_set(
        self,
        ctx: discord.ApplicationContext,
        owner_prefix: discord.Option(
            str,
            description="Role given to VC Owners",
        ),
    ):
        self.bot.repos.guild_settings.edit(ctx.guild_id, owner_prefix=owner_prefix)
        await ctx.respond(f"Owner prefix set to `{owner_prefix}`")

    @owner.command(name="prefix-clear", description="Set a prefix given to owners of a Temp Channel")
    async def prefix_clear(
        self,
        ctx: discord.ApplicationContext,
    ):
        self.bot.repos.guild_settings.edit(ctx.guild_id, owner_prefix=0)
        await ctx.respond(f"Owner prefix has been cleared.")

    @owner.command(name="prefix-get", description="Get the currently selected prefix given to owners of Temp Channels")
    async def prefix_get(
        self,
        ctx: discord.ApplicationContext
    ):

        settings = self.bot.repos.guild_settings.get(ctx.guild_id)
        if settings is None:
            await ctx.respond(f"Owner prefix could not be retrieved.")
            return

        owner_prefix = settings["owner_prefix"]
        if owner_prefix is None:
            await ctx.respond(f"Owner prefix is not set.")
            return

        await ctx.respond(f"Owner prefix set to `{owner_prefix}`")

    placeholder = settings.create_subgroup(
        "placeholder",
        "Manage custom channel name placeholders",
    )

    @placeholder.command(name="add", description="Add a custom channel name placeholder")
    async def add_placeholder(
        self,
        ctx: discord.ApplicationContext,
    ):
        await ctx.send_modal(PlaceholderAddModal(self.bot, ctx))

        embed = discord.Embed(
            title="",
            description=f"Make sure to click \"SUBMIT\" after editing the pop-up menu.",
            color=discord.Color.yellow()
        )
        embed.set_footer(text="This message will disappear in 30 seconds.")
        reply = await ctx.send_followup(embed=embed, ephemeral=True, wait=True)
        await reply.delete(delay=30)

    @placeholder.command(name="list", description="List custom channel name placeholders")
    async def list_placeholder(
        self,
        ctx: discord.ApplicationContext,
    ):
        placeholders = self.bot.repos.placeholders.get_all(ctx.guild.id)
        if not placeholders:
            await ctx.respond("No custom placeholders configured.", ephemeral=True)
            return

        lines = []
        for entry in placeholders:
            role = ctx.guild.get_role(entry["role_id"]) if entry["role_id"] else None
            lines.append(
                f"`{entry['placeholder']}` → `{entry['replace_text']}` if user has {role.mention if role else "`None`"}"
            )

        embed = discord.Embed(
            title=f"Custom Placeholders ({len(placeholders)})",
            description="\n".join(lines),
            color=discord.Color.blue(),
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @placeholder.command(name="remove", description="Remove a custom channel name placeholder")
    async def remove_placeholder(
        self,
        ctx: discord.ApplicationContext,
        entry: discord.Option(
            str,
            description="Select the placeholder entry to remove",
            autocomplete=placeholder_remove_autocomplete,
        ),
    ):
        try:
            entry_id = int(entry)
        except (TypeError, ValueError):
            await ctx.respond("Invalid selection. Pick an entry from the list.", ephemeral=True)
            return

        existing = self.bot.repos.placeholders.get(ctx.guild.id, entry_id)
        if not existing:
            await ctx.respond("No matching placeholder entry found.", ephemeral=True)
            return

        self.bot.repos.placeholders.remove(ctx.guild.id, entry_id)
        await ctx.respond(
            f"Removed `{existing['placeholder']}` → `{existing['replace_text']}`.",
            ephemeral=True,
        )


def setup(bot):
    bot.add_cog(SettingsMenuCog(bot))
