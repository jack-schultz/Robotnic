import discord
from discord.ext import commands
from cogs.settings.modals import ControlsModal, LogsModal
from cogs.settings.placeholders.modals import PlaceholderAddModal
from config.i18n import t, available_languages, command_kwargs, localizations


async def placeholder_remove_autocomplete(ctx: discord.AutocompleteContext):
    guild = ctx.interaction.guild
    lang = ctx.bot.repos.guild_settings.get_language(guild.id)
    entries = ctx.bot.repos.placeholders.get_all(guild.id)
    query = (ctx.value or "").lower()
    choices = []
    for entry in entries:
        role = guild.get_role(entry["role_id"]) if entry["role_id"] else None
        # en: "'{placeholder}' → '{replace_text}' for role: '{role}'"
        label = t(
            "settings.placeholder.autocomplete", lang,
            placeholder=entry["placeholder"],
            replace_text=entry["replace_text"],
            role=role.name if role else t("common.none", lang),
        )
        if query and query not in label.lower():
            continue
        choices.append(discord.OptionChoice(name=label[:100], value=str(entry["id"])))
        if len(choices) >= 25:
            break
    return choices


class SettingsMenuCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _lang(self, ctx):
        return self.bot.repos.guild_settings.get_language(ctx.guild_id)

    async def _send_submit_reminder(self, ctx):
        lang = self._lang(ctx)
        embed = discord.Embed(
            title="",
            description=t("common.submit_reminder", lang),
            color=discord.Color.yellow()
        )
        embed.set_footer(text=t("common.disappear_seconds", lang, seconds=30))
        reply = await ctx.send_followup(embed=embed, ephemeral=True, wait=True)
        await reply.delete(delay=30)

    settings = discord.SlashCommandGroup(
        **command_kwargs("commands.settings"),
        default_member_permissions=discord.Permissions(manage_channels=True),
    )

    @settings.command(**command_kwargs("commands.settings.logging"))
    async def logging(
            self,
            ctx: discord.ApplicationContext,
    ):
        await ctx.send_modal(LogsModal(self.bot, ctx))
        await self._send_submit_reminder(ctx)

    @settings.command(**command_kwargs("commands.settings.controls"))
    async def controls(
        self,
        ctx: discord.ApplicationContext,
    ):
        await ctx.send_modal(ControlsModal(self.bot, ctx))
        await self._send_submit_reminder(ctx)

    @settings.command(**command_kwargs("commands.settings.profanity_filter"))
    async def profanity_filter(
        self,
        ctx: discord.ApplicationContext,
        mode: discord.Option(
            str,
            choices=[
                discord.OptionChoice(
                    name=t(f"commands.settings.profanity_filter.choice.{key}"),
                    value=value,
                    name_localizations=localizations(f"commands.settings.profanity_filter.choice.{key}"),
                )
                for key, value in (("off", "off"), ("alert", "alert"), ("alert_block", "alert & block"))
            ],
            **command_kwargs("commands.settings.profanity_filter.mode")
        )
    ):
        self.bot.repos.guild_settings.edit(ctx.guild_id, profanity_filter=mode)
        await ctx.respond(
            t("settings.profanity_filter.set", self._lang(ctx), mode=mode)
        )

    @settings.command(**command_kwargs("commands.settings.language"))
    async def language(
        self,
        ctx: discord.ApplicationContext,
        language: discord.Option(
            str,
            choices=[
                discord.OptionChoice(name=name, value=code)
                for code, name in available_languages().items()
            ],
            **command_kwargs("commands.settings.language.language")
        )
    ):
        self.bot.repos.guild_settings.edit(ctx.guild_id, language=language)
        # Responds in the newly selected language
        await ctx.respond(
            t("settings.language.set", language, language=available_languages()[language])
        )

    owner = settings.create_subgroup(
        **command_kwargs("commands.settings.owner"),
    )

    @owner.command(**command_kwargs("commands.settings.owner.dm_on_create"))
    async def dm_owner(
        self,
        ctx: discord.ApplicationContext,
        enabled: discord.Option(
            bool,
            **command_kwargs("commands.settings.owner.dm_on_create.enabled"),
        ),
    ):
        self.bot.repos.guild_settings.edit(ctx.guild_id, dm_owner=enabled)
        await ctx.respond(t("settings.owner.dm_set", self._lang(ctx), enabled=enabled))

    @owner.command(**command_kwargs("commands.settings.owner.role_set"))
    async def role_set(
        self,
        ctx: discord.ApplicationContext,
        owner_role: discord.Option(
            discord.Role,
            **command_kwargs("commands.settings.owner.role_set.owner_role"),
        ),
    ):
        self.bot.repos.guild_settings.edit(ctx.guild_id, owner_role_id=owner_role.id)
        await ctx.respond(t("settings.owner.role_set", self._lang(ctx), name=owner_role.name, id=owner_role.id))

    @owner.command(**command_kwargs("commands.settings.owner.role_clear"))
    async def role_clear(
        self,
        ctx: discord.ApplicationContext,
    ):
        self.bot.repos.guild_settings.edit(ctx.guild_id, owner_role_id=0)
        await ctx.respond(t("settings.owner.role_cleared", self._lang(ctx)))

    @owner.command(**command_kwargs("commands.settings.owner.role_get"))
    async def role_get(
        self,
        ctx: discord.ApplicationContext
    ):
        lang = self._lang(ctx)
        settings = self.bot.repos.guild_settings.get(ctx.guild_id)
        if settings is None:
            await ctx.respond(t("settings.owner.role_unavailable", lang))
            return

        owner_role_id = settings["owner_role_id"]
        if owner_role_id is None or owner_role_id == 0:
            await ctx.respond(t("settings.owner.role_not_set", lang))
            return

        owner_role = ctx.guild.get_role(owner_role_id)
        if owner_role is None:
            await ctx.respond(t("settings.owner.role_unavailable", lang))
            return

        await ctx.respond(t("settings.owner.role_set", lang, name=owner_role.name, id=owner_role.id))

    @owner.command(**command_kwargs("commands.settings.owner.prefix_set"))
    async def role_set(
        self,
        ctx: discord.ApplicationContext,
        owner_prefix: discord.Option(
            str,
            **command_kwargs("commands.settings.owner.prefix_set.owner_prefix"),
        ),
    ):
        self.bot.repos.guild_settings.edit(ctx.guild_id, owner_prefix=owner_prefix)
        await ctx.respond(t("settings.owner.prefix_set", self._lang(ctx), prefix=owner_prefix))

    @owner.command(**command_kwargs("commands.settings.owner.prefix_clear"))
    async def prefix_clear(
        self,
        ctx: discord.ApplicationContext,
    ):
        self.bot.repos.guild_settings.edit(ctx.guild_id, owner_prefix=0)
        await ctx.respond(t("settings.owner.prefix_cleared", self._lang(ctx)))

    @owner.command(**command_kwargs("commands.settings.owner.prefix_get"))
    async def prefix_get(
        self,
        ctx: discord.ApplicationContext
    ):
        lang = self._lang(ctx)
        settings = self.bot.repos.guild_settings.get(ctx.guild_id)
        if settings is None:
            await ctx.respond(t("settings.owner.prefix_unavailable", lang))
            return

        owner_prefix = settings["owner_prefix"]
        if owner_prefix is None:
            await ctx.respond(t("settings.owner.prefix_not_set", lang))
            return

        await ctx.respond(t("settings.owner.prefix_set", lang, prefix=owner_prefix))

    placeholder = settings.create_subgroup(
        **command_kwargs("commands.settings.placeholder"),
    )

    @placeholder.command(**command_kwargs("commands.settings.placeholder.add"))
    async def add_placeholder(
        self,
        ctx: discord.ApplicationContext,
    ):
        await ctx.send_modal(PlaceholderAddModal(self.bot, ctx))
        await self._send_submit_reminder(ctx)

    @placeholder.command(**command_kwargs("commands.settings.placeholder.list"))
    async def list_placeholder(
        self,
        ctx: discord.ApplicationContext,
    ):
        lang = self._lang(ctx)
        placeholders = self.bot.repos.placeholders.get_all(ctx.guild.id)
        if not placeholders:
            await ctx.respond(t("settings.placeholder.none_configured", lang), ephemeral=True)
            return

        lines = []
        for entry in placeholders:
            role = ctx.guild.get_role(entry["role_id"]) if entry["role_id"] else None
            lines.append(
                t(
                    "settings.placeholder.list_line", lang,
                    placeholder=entry["placeholder"],
                    replace_text=entry["replace_text"],
                    role=role.mention if role else t("common.none_code", lang),
                )
            )

        embed = discord.Embed(
            title=t("settings.placeholder.list_title", lang, count=len(placeholders)),
            description="\n".join(lines),
            color=discord.Color.blue(),
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @placeholder.command(**command_kwargs("commands.settings.placeholder.remove"))
    async def remove_placeholder(
        self,
        ctx: discord.ApplicationContext,
        entry: discord.Option(
            str,
            **command_kwargs("commands.settings.placeholder.remove.entry"),
            autocomplete=placeholder_remove_autocomplete,
        ),
    ):
        lang = self._lang(ctx)
        try:
            entry_id = int(entry)
        except (TypeError, ValueError):
            await ctx.respond(t("settings.placeholder.invalid_selection", lang), ephemeral=True)
            return

        existing = self.bot.repos.placeholders.get(ctx.guild.id, entry_id)
        if not existing:
            await ctx.respond(t("settings.placeholder.not_found", lang), ephemeral=True)
            return

        self.bot.repos.placeholders.remove(ctx.guild.id, entry_id)
        await ctx.respond(
            t("settings.placeholder.removed", lang, placeholder=existing["placeholder"], replace_text=existing["replace_text"]),
            ephemeral=True,
        )


def setup(bot):
    bot.add_cog(SettingsMenuCog(bot))
