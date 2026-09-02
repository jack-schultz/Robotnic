import logging
import discord

logger = logging.getLogger(__name__)


def get_child_category(db_info, creator_channel, bot, guild_name):
    if db_info.child_category_id != 0:
        category = bot.get_channel(db_info.child_category_id)
        if category is None:
            logger.warning(
                f"Configured child category {db_info.child_category_id} not found for creator channel {creator_channel.id} in guild '{guild_name}'"
            )
        logger.debug(
            f"Using configured child category {db_info.child_category_id} "
            f"({category.name if category else 'not found'}) for creator channel {creator_channel.id} in guild '{guild_name}'"
        )
    else:
        category = creator_channel.category
        logger.debug(
            f"Using creator channel category "
            f"({category.name if category else 'none'}) for creator channel {creator_channel.id} "
            f"in guild '{guild_name}'"
        )
    return category


def get_child_overwrites(db_info, creator_channel, category, guild_name):
    # 0 -> no overwrites
    # 1 -> overwrites from creator
    # 2 -> overwrites from category
    if db_info.child_overwrites == 1:
        overwrites = creator_channel.overwrites
        logger.debug(f"Using creator channel overwrites for temp channel in {creator_channel.id} in guild '{guild_name}'")
    elif db_info.child_overwrites == 2:
        if category:
            overwrites = category.overwrites
            logger.debug(f"Using category overwrites from {category.name} for temp channel in {creator_channel.id} in guild '{guild_name}'")
        else:
            overwrites = creator_channel.overwrites
            logger.warning(
                f"No category available for overwrite source, falling back to creator channel overwrites for {creator_channel.id} in guild '{guild_name}'"
            )
    else:
        overwrites = {}
        logger.debug(f"Using no inherited overwrites for temp channel in {creator_channel.id} in guild '{guild_name}'")
    return overwrites


def collate_temp_channel_overwrites(overwrites, bot_user, member):
    overwrites[bot_user] = discord.PermissionOverwrite(
        view_channel=True,
        manage_channels=True,
        send_messages=True,
        manage_messages=True,
        read_message_history=True,
        connect=True,
        move_members=True,
    )
    overwrites[member] = discord.PermissionOverwrite(
        view_channel=True,
        send_messages=True,
        read_message_history=True,
        connect=True,
    )
