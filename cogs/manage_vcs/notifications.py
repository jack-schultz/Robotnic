import logging
import datetime
import discord
from cogs.manage_vcs.views.dm_owner_button import AcknowledgeButtonView
from config.i18n import t

logger = logging.getLogger(__name__)


async def dm_user_on_create(bot, temp_channel, member, control_view):
    if bot.repos.user_notifications.get_dm_owner_controls(member.id):
        return

    guild_settings = bot.repos.guild_settings.get(temp_channel.guild.id)
    if not guild_settings["dm_owner_bool"]:
        return

    lang = guild_settings["language"]
    message_jump_link = f"https://discord.com/channels/{temp_channel.guild.id}/{temp_channel.id}/{control_view.message.id}"

    embed = discord.Embed(
        title=t("owner.dm.title", lang),
        description=t("owner.dm.description", lang, link=message_jump_link),
        color=discord.Color.green(),
    )
    embed.add_field(
        name=t("owner.dm.controls_title", lang),
        value=t("owner.dm.controls_value", lang),
        inline=False,
    )

    await member.send(
        embed=embed,
        view=AcknowledgeButtonView(message_jump_link, lang),
    )


async def send_temp_channel_create_logs(bot, temp_channel, member, guild_name):
    lang = bot.repos.guild_settings.get_language(temp_channel.guild.id)
    embed = discord.Embed(
        title=t("guild_log.create_title", lang),
        description="",
        color=discord.Color.green()
    )
    embed.add_field(
        name=t("guild_log.channel", lang),
        value=t("guild_log.channel_value", lang, name=temp_channel.name, id=temp_channel.id),
        inline=False
    )
    embed.add_field(
        name=t("guild_log.user", lang),
        value=t("guild_log.member_value", lang, member=member, id=member.id),
        inline=False
    )
    embed.timestamp = datetime.datetime.now()
    await bot.GuildLogService.send(
        event="channel_create",
        guild=temp_channel.guild,
        message=f"",
        embed=embed
    )
    await bot.BotLogService.send(
        event="channel_create",
        message=t("bot_log.channel_created", channel=temp_channel.name, guild=member.guild.name, user=member)
    )
    logger.debug(f"Sent create logs for temp channel {temp_channel.name} ({temp_channel.id}) in guild '{guild_name}'")


async def send_temp_channel_remove_logs(bot, old_temp_channel, member, guild_name):
    lang = bot.repos.guild_settings.get_language(member.guild.id)
    embed = discord.Embed(
        title=t("guild_log.remove_title", lang),
        description="",
        color=discord.Color.orange()
    )
    embed.add_field(
        name=t("guild_log.channel", lang),
        value=t("guild_log.channel_value", lang, name=old_temp_channel.name, id=old_temp_channel.id),
        inline=False
    )
    embed.add_field(
        name=t("guild_log.last_connected_user", lang),
        value=t("guild_log.member_value", lang, member=member, id=member.id),
        inline=False
    )
    embed.timestamp = datetime.datetime.now()
    await bot.GuildLogService.send(
        event="channel_remove",
        guild=member.guild, message=f"",
        embed=embed
    )
    await bot.BotLogService.send(
        event="channel_remove",
        message=t("bot_log.channel_removed", guild=member.guild.name, user=member)
    )
    logger.debug(f"Sent remove logs for temp channel {old_temp_channel.name} ({old_temp_channel.id}) in guild '{guild_name}'")
