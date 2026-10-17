import logging
import datetime
import discord
import requests
from cogs.manage_vcs.update_name import update_channel_name_and_control_msg
from config.i18n import t, command_text, fit_limit, MODAL_TITLE_LIMIT, LABEL_LIMIT, PLACEHOLDER_LIMIT

logger = logging.getLogger(__name__)


async def check_profanity(session, text: str) -> dict | None:
    try:
        response = session.post(
            "https://vector.profanity.dev",
            json={"message": text},
            timeout=3,
        )
        data = response.json()
    except Exception as e:
        logger.warning(f"Profanity API failed, skipping check. {e}")
        return None

    # The API sometimes answers with JSON null instead of an object
    if not isinstance(data, dict):
        logger.warning(f"Profanity API returned {type(data).__name__}, skipping check.")
        return None
    return data


class ChangeNameModal(discord.ui.Modal):
    def __init__(self, bot, channel):
        self.lang = bot.repos.guild_settings.get_language(channel.guild.id)
        super().__init__(title=fit_limit(t("control.rename.modal_title", self.lang), MODAL_TITLE_LIMIT))
        self.bot = bot
        self.channel = channel

        # Define the text inputs
        self.channel_name = discord.ui.InputText(
            label=fit_limit(t("control.rename.label", self.lang), LABEL_LIMIT),
            placeholder=fit_limit(f"{channel.name}", PLACEHOLDER_LIMIT),
            required=False,
            max_length=25
        )

        self.add_item(self.channel_name)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # Update the channel
        channel_name = str(self.channel_name.value or self.channel.name)
        if len(channel_name) > 100:
            channel_name = channel_name[:97] + "..."

        profanity_check_setting = self.bot.repos.guild_settings.get_profanity_filter(interaction.guild.id)["profanity_filter"]
        if profanity_check_setting is not None:
            profanity_check = await check_profanity(requests, channel_name)

            if profanity_check is not None and profanity_check.get("isProfanity"):
                embed = discord.Embed(
                    title=t("guild_log.blocked_rename_title", self.lang),
                    description="",
                    color=discord.Color.red()
                )
                embed.add_field(name=t("guild_log.channel", self.lang),
                                value=t("guild_log.channel_value", self.lang, name=self.channel.name, id=self.channel.id),
                                inline=False)
                embed.add_field(name=t("guild_log.user", self.lang),
                                value=t("guild_log.user_value", self.lang, display_name=interaction.user.display_name, id=interaction.user.id),
                                inline=False)
                embed.add_field(name=t("guild_log.new_name_blocked", self.lang),
                                value=f"`{channel_name}`",
                                inline=False)
                embed.add_field(name=t("guild_log.flagged_for", self.lang),
                                value=f"`{profanity_check.get("flaggedFor")}`",
                                inline=False)
                embed.timestamp = datetime.datetime.now()
                embed.set_footer(text=t("guild_log.toggle_footer", self.lang, command=command_text("commands.settings", "commands.settings.profanity_filter", language=self.lang)))
                await self.bot.GuildLogService.send(event="profanity_block", guild=interaction.guild, message=f"", embed=embed)

                if profanity_check_setting == "alert & block":
                    try:
                        reply = await interaction.followup.send(
                            t("control.rename.profanity_blocked", self.lang),
                            ephemeral=True,
                            wait=True,
                        )
                        await reply.delete(delay=90)
                    except (discord.NotFound, discord.HTTPException):
                        pass
                    return

        # If inputted name, schedule update channel and update db
        if self.channel_name.value:
            await self.bot.TempChannelRenamer.schedule(self.channel, channel_name)
            await self.bot.EmbedUpdateScheduler.schedule(self.channel, title=channel_name)
            self.bot.repos.temp_channels.set_is_renamed(self.channel.id, True)
        else:
            # If left blank the channel rename override is reset
            self.bot.repos.temp_channels.set_is_renamed(self.channel.id, False)
            await update_channel_name_and_control_msg(self.bot, [self.channel.id])

        embed = discord.Embed(
            title=t("common.changes_saved", self.lang),
            description=t("control.rename.saved_description", self.lang),
            color=discord.Color.blue()
        )
        embed.set_footer(text=t("common.disappear_seconds", self.lang, seconds=30))
        try:
            reply = await interaction.followup.send(embed=embed, ephemeral=True, wait=True)
            await reply.delete(delay=30)
        except (discord.NotFound, discord.HTTPException):
            pass

        # Sends messages in the guild log channel - uses get_guild_logs_channel_id instead of get_guild_settings for read efficiency
        embed = discord.Embed(
            title=t("guild_log.rename_title", self.lang),
            description="",
            color=discord.Color.yellow()
        )
        embed.add_field(name=t("guild_log.old_channel", self.lang),
                        value=t("guild_log.channel_value", self.lang, name=self.channel.name, id=self.channel.id),
                        inline=False)
        embed.add_field(name=t("guild_log.user", self.lang),
                        value=t("guild_log.user_value", self.lang, display_name=interaction.user.display_name, id=interaction.user.id),
                        inline=False)
        embed.add_field(name=t("guild_log.new_name", self.lang),
                        value=f"`{channel_name}`",
                        inline=False)
        embed.timestamp = datetime.datetime.now()
        await self.bot.GuildLogService.send(event="channel_rename", guild=interaction.guild, message=f"", embed=embed)
