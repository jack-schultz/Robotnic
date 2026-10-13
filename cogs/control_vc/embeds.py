import discord
from cogs.control_vc.enums import ChannelState
from cogs.manage_vcs.create_name import create_temp_channel_name
from config.i18n import t


class ControlIconsEmbed(discord.Embed):
    def __init__(self, bot, channel):
        super().__init__(
            title="",
            description="",
            color=0x00ff00
        )

        lang = bot.repos.guild_settings.get_language(channel.guild.id)
        for control in ("rename", "limit", "give", "clear", "ban", "mute", "deafen", "delete"):
            self.add_field(name=t(f"control.icons.{control}", lang), value="", inline=True)
        control_options = bot.repos.guild_settings.get(channel.guild.id)["control_options"]
        if "state_changeable" in control_options:
            for control in ("public", "hide", "lock"):
                self.add_field(name=t(f"control.icons.{control}", lang), value="", inline=True)


class ChannelInfoEmbed(discord.Embed):
    def __init__(self, bot, temp_channel, title=None, user_limit=None):
        super().__init__(
            color=discord.Color.blue()
        )

        lang = bot.repos.guild_settings.get_language(temp_channel.guild.id)
        temp_channel_info = bot.repos.temp_channels.get_info(temp_channel.id)

        # title input incase it was just changed and propagated to channel yet
        self.title = title
        if not self.title:
            if temp_channel_info is not None and temp_channel_info.is_renamed:
                self.title = f"{temp_channel.name}"
            elif temp_channel_info is not None:
                self.title = create_temp_channel_name(bot, temp_channel)
            else:
                self.title = temp_channel.name

        self.footer = discord.EmbedFooter(t("control.info.footer", lang))

        owner_id = temp_channel_info.owner_id if temp_channel_info is not None else None
        if owner_id:
            if owner_id is not None:
                owner = f"<@{owner_id}>"
            else:
                owner = t("control.info.no_owner", lang)
        else:
            owner = t("control.info.no_owner", lang)
        self.add_field(name=t("control.info.owner", lang), value=f"{owner}", inline=True)

        if not user_limit:
            user_limit = temp_channel.user_limit
        if user_limit == 0:
            user_limit = t("control.info.unlimited", lang)
        self.add_field(name=t("control.info.user_limit", lang), value=f"{user_limit}", inline=True)

        # region = temp_channel.rtc_region
        # if region is None:
        #     region = "🌍 Auto"
        # self.add_field(name="Region", value=f"{region}", inline=True)

        control_options = bot.repos.guild_settings.get(temp_channel.guild.id)["control_options"]
        if "state_changeable" in control_options:
            channel_state_id = temp_channel_info.channel_state if temp_channel_info is not None else None
            if channel_state_id == ChannelState.PUBLIC.value:
                channel_state = t("control.info.public", lang)
            elif channel_state_id == ChannelState.LOCKED.value:
                channel_state = t("control.info.locked", lang)
            elif channel_state_id == ChannelState.HIDDEN.value:
                channel_state = t("control.info.hidden", lang)
            else:
                channel_state = t("common.none", lang)
            self.add_field(name=t("control.info.access", lang), value=f"{channel_state}", inline=True)
