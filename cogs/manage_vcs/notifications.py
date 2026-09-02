import logging
import datetime
import discord
from cogs.manage_vcs.views.dm_owner_button import AcknowledgeButtonView

logger = logging.getLogger(__name__)


async def dm_user_on_create(bot, temp_channel, member, control_view):
    embed = discord.Embed(
        title="You Are The Admin of Your Channel",
        description=f"As the owner of <#{temp_channel.id}> you can moderate the users you are in a call with. To view your control panel, click [here]({control_view.message.jump_url})",
        color=discord.Color.green()
    )
    embed.add_field(name="Kick a Member", value=f"`{temp_channel.name}` (`{temp_channel.id}`)",)
    await member.send(f"", embed=embed, view=AcknowledgeButtonView())


async def send_temp_channel_create_logs(bot, temp_channel, member, guild_name):
    embed = discord.Embed(
        title="TempChannel Create",
        description="",
        color=discord.Color.green()
    )
    embed.add_field(
        name="Channel",
        value=f"`{temp_channel.name}` (`{temp_channel.id}`)",
        inline=False
    )
    embed.add_field(
        name="User",
        value=f"`{member}` (`{member.id}`)",
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
        message=f"Temp Channel (`{temp_channel.name}`) was made in server (`{member.guild.name}`) by user (`{member}`)"
    )
    logger.debug(f"Sent create logs for temp channel {temp_channel.name} ({temp_channel.id}) in guild '{guild_name}'")


async def send_temp_channel_remove_logs(bot, old_temp_channel, member, guild_name):
    embed = discord.Embed(
        title="TempChannel Removed",
        description="",
        color=discord.Color.orange()
    )
    embed.add_field(
        name="Channel",
        value=f"`{old_temp_channel.name}` (`{old_temp_channel.id}`)",
        inline=False
    )
    embed.add_field(
        name="Last Connected User",
        value=f"`{member}` (`{member.id}`)",
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
        message=f"Temp Channel was removed in server (`{member.guild.name}`) by user (`{member}`)"
    )
    logger.debug(f"Sent remove logs for temp channel {old_temp_channel.name} ({old_temp_channel.id}) in guild '{guild_name}'")
