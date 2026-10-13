import discord
from config.i18n import t, command_text


def _add_joined_date(embed, guild):
    me = guild.me
    if me is None or me.joined_at is None:
        return
    unix_time = int(me.joined_at.timestamp())
    embed.add_field(name=t("bot_log.joined_date"), value=f"<t:{unix_time}:f>\n<t:{unix_time}:R>", inline=True)


async def on_guild_join(bot, guild):
    lang = bot.repos.guild_settings.get_language(guild.id)

    # This event is triggered when the bot joins a new guild
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            embed = discord.Embed(
                title=t("guild_join.title", lang, guild=guild.name),
                description=t("guild_join.description", lang),
                color=discord.Color.blue()
            )
            embed.add_field(
                name=command_text("commands.setup", language=lang),
                value=t("guild_join.setup", lang),
                inline=False
            )
            embed.add_field(
                name=command_text("commands.help", language=lang),
                value=t("guild_join.help", lang),
                inline=False
            )
            embed.set_footer(text=t("guild_join.footer", lang))
            view = discord.ui.View()
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.url,
                                            label=t("guild_join.contact_support", lang),
                                            url=f"https://discord.gg/rcAREJyMV5"))
            # view.add_item(discord.ui.Button(style=discord.ButtonStyle.url,
            #                                 label="Visit Website",
            #                                 url=f"link"))
            await channel.send(t("guild_join.message", lang), embed=embed, view=view)
            break

    # Create the embed with the server information
    embed = discord.Embed(
        title=t("bot_log.guild_joined"),
        description=f"",
        color=discord.Color.green()
    )
    embed.add_field(name=t("bot_log.server_name"), value=guild.name, inline=True)
    embed.add_field(name=t("bot_log.server_id"), value=guild.id, inline=True)
    embed.add_field(name=t("bot_log.owner"), value=t("bot_log.owner_value", owner=guild.owner, owner_id=guild.owner_id), inline=True)
    embed.add_field(name=t("bot_log.member_count"), value=guild.member_count, inline=True)
    embed.add_field(name=t("bot_log.text_channel_count"), value=str(len(guild.text_channels)), inline=True)
    embed.add_field(name=t("bot_log.locale"), value=str(guild.preferred_locale), inline=True)
    unix_time = int(guild.created_at.timestamp())
    embed.add_field(name=t("bot_log.creation_date"), value=f"<t:{unix_time}:f>\n<t:{unix_time}:R>", inline=True)
    _add_joined_date(embed, guild)
    await bot.BotLogService.send(event="guild_join", message=f"", embed=embed)


async def on_guild_remove(bot, guild):
    # Create the embed with the server information
    embed = discord.Embed(
        title=t("bot_log.guild_left"),
        description=f"",
        color=discord.Color.red()
    )
    embed.add_field(name=t("bot_log.server_name"), value=guild.name, inline=True)
    embed.add_field(name=t("bot_log.server_id"), value=guild.id, inline=True)
    embed.add_field(name=t("bot_log.owner"), value=t("bot_log.owner_value", owner=guild.owner, owner_id=guild.owner_id), inline=True)
    embed.add_field(name=t("bot_log.member_count"), value=guild.member_count, inline=True)
    embed.add_field(name=t("bot_log.text_channel_count"), value=str(len(guild.text_channels)), inline=True)
    embed.add_field(name=t("bot_log.locale"), value=str(guild.preferred_locale), inline=True)
    unix_time = int(guild.created_at.timestamp())
    embed.add_field(name=t("bot_log.creation_date"), value=f"<t:{unix_time}:f>\n<t:{unix_time}:R>", inline=True)
    _add_joined_date(embed, guild)
    await bot.BotLogService.send(event="guild_leave", message=f"", embed=embed)
