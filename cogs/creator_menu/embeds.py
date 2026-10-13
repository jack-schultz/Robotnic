import discord
from config.i18n import t


class OptionsEmbed(discord.Embed):
    def __init__(self, lang):
        super().__init__(
            title=t("creator_menu.options.title", lang),
            color=discord.Color.blue()
        )
        self.set_footer(text=t("common.disappear_seconds", lang, seconds=120))
        self.add_field(name=t("creator_menu.options.child_name", lang), value=t("creator_menu.options.child_name_value", lang), inline=False)
        self.add_field(name=t("creator_menu.options.user_limit", lang), value=t("creator_menu.options.user_limit_value", lang), inline=False)
        self.add_field(name=t("creator_menu.options.permissions", lang), value=t("creator_menu.options.permissions_value", lang), inline=False)
        self.add_field(name=t("creator_menu.options.category", lang), value=t("creator_menu.options.category_value", lang), inline=False)


class ListCreatorsEmbed(discord.Embed):
    def __init__(self, guild, bot):
        lang = bot.repos.guild_settings.get_language(guild.id)
        super().__init__(
            title=t("creator_menu.list.title", lang),
            color=discord.Color.green()
        )

        # Creates a field for each creator channel
        creator_channel_ids = bot.repos.creator_channels.get_ids(guild_id=guild.id)
        for i, channel_id in enumerate(creator_channel_ids):
            channel = bot.get_channel(channel_id)
            creator_info = bot.repos.creator_channels.get_info(channel_id)

            if channel:
                child_name = creator_info.child_name
                user_limit = t("common.unlimited", lang) if creator_info.user_limit == 0 else creator_info.user_limit
                category = t("creator_menu.list.same_as_creator", lang) if creator_info.child_category_id == 0 else bot.get_channel(creator_info.child_category_id)
                if creator_info.child_overwrites == 1:
                    overwrites = t("creator_menu.list.copy_creator_channel", lang)
                elif creator_info.child_overwrites == 2:
                    overwrites = t("creator_menu.list.copy_creator_category", lang)
                else:  # should be for case 0
                    overwrites = t("common.none", lang)

                desc = t("creator_menu.list.entry", lang, child_name=child_name, user_limit=user_limit, overwrites=overwrites, category=category)
                self.add_field(name=f"#{i+1}. {channel.mention}", value=desc, inline=True)

        # Handle case of no fields. Also prevents error of no embed content
        if len(self.fields) < 1:
            self.title = t("creator_menu.list.empty", lang)
