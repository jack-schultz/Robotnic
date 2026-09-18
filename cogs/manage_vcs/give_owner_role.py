import logging
import discord

logger = logging.getLogger(__name__)


async def give_owner_role(bot, member):
    guild_name = member.guild.name
    settings = bot.repos.guild_settings.get(member.guild.id)
    if settings is None:
        logger.debug(
            f"Skipping owner role for {member} in guild '{guild_name}': no guild settings."
        )
        return

    owner_role_id = settings["owner_role_id"]
    if owner_role_id is None:
        logger.debug(
            f"Skipping owner role for {member} in guild '{guild_name}': owner role not configured."
        )
        return

    owner_role = member.guild.get_role(owner_role_id)
    if owner_role is None:
        logger.warning(
            f"Configured owner role {owner_role_id} not found for {member} in guild '{guild_name}'"
        )
        return

    me = member.guild.me
    if not me.guild_permissions.manage_roles:
        logger.warning(
            f"Missing `manage_roles` permission to assign owner role `{owner_role.name}` to {member} in guild '{guild_name}'"
        )
        return

    # Bot cannot manage roles equal to or higher than its highest role
    if owner_role >= me.top_role:
        logger.warning(
            f"Cannot assign owner role `{owner_role.name}` to {member} in guild '{guild_name}': "
            f"role is equal to or higher than the bot's top role `{me.top_role.name}`"
        )
        return

    # Don't try to add a role the member already has
    if owner_role in member.roles:
        logger.debug(
            f"{member} already has owner role `{owner_role.name}` in guild '{guild_name}', skipping."
        )
        return

    try:
        await member.add_roles(owner_role, reason="Owner role assignment")
        logger.debug(
            f"Assigned owner role `{owner_role.name}` to {member} in guild '{guild_name}'"
        )
    except discord.Forbidden as e:
        logger.warning(
            f"Permission error assigning owner role `{owner_role.name}` to {member} in guild '{guild_name}'. {e}"
        )
    except discord.HTTPException as e:
        logger.debug(
            f"Could not assign owner role `{owner_role.name}` to {member} in guild '{guild_name}'. {e}"
        )
