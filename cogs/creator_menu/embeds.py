import math
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


# Discord allows at most 25 embed fields, 25 select options and 6000 characters across a message's embeds.
# Each creator entry can be ~350 characters, so 9 per page (a 3x3 grid of inline fields) stays well under all three.
CREATORS_PER_PAGE = 9


def get_creator_channels(bot, guild):
    """Returns the guild's creator channels that still exist, in list order."""
    channels = []
    for channel_id in bot.repos.creator_channels.get_ids(guild_id=guild.id):
        channel = bot.get_channel(channel_id)
        if channel:
            channels.append(channel)
    return channels


def page_count(total):
    """Number of pages needed to list `total` creators. Always at least 1 so an empty list still has a page."""
    return max(1, math.ceil(total / CREATORS_PER_PAGE))


class ListCreatorsEmbed(discord.Embed):
    def __init__(self, bot, guild, numbered_creators, page, pages):
        """
        numbered_creators: (number, channel) pairs for the creators on this page
        page: 0-based index of this page, pages: total number of pages
        """
        lang = bot.repos.guild_settings.get_language(guild.id)
        super().__init__(
            title=t("creator_menu.list.title", lang),
            color=discord.Color.green()
        )

        # Creates a field for each creator channel on this page
        for number, channel in numbered_creators:
            creator_info = bot.repos.creator_channels.get_info(channel.id)

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
            self.add_field(name=f"#{number}. {channel.mention}", value=desc, inline=True)

        if pages > 1:
            self.set_footer(text=t("creator_menu.list.page", lang, page=page + 1, pages=pages))

        # Handle case of no fields. Also prevents error of no embed content
        if len(self.fields) < 1:
            self.title = t("creator_menu.list.empty", lang)
