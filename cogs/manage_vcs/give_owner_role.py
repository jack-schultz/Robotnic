import discord


async def give_owner_role(bot, member):
    settings = bot.repos.guild_settings.get(member.guild.id)
    if settings is None:
        return

    owner_role_id = settings["owner_role_id"]
    if owner_role_id is None:
        return

    owner_role = member.guild.get_role(owner_role_id)
    if owner_role is None:
        return

    me = member.guild.me
    if not me.guild_permissions.manage_roles:
        return

    # Bot cannot manage roles equal to or higher than its highest role
    if owner_role >= me.top_role:
        return

    # Don't try to add a role the member already has
    if owner_role in member.roles:
        return

    try:
        await member.add_roles(owner_role, reason="Owner role assignment")
    except discord.Forbidden:
        return
    except discord.HTTPException:
        return
