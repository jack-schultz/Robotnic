import discord


def create_temp_channel_name(bot, temp_channel, db_temp_channel_info=None, db_creator_channel_info=None):
    if not temp_channel:
        bot.logger.debug("Skipping temp channel name generation: temp_channel is None.")
        return None

    # Allows db info to be passed in if it was already retrieved for something else. Choice reduces db reads
    if not db_temp_channel_info:
        db_temp_channel_info = bot.repos.temp_channels.get_info(temp_channel.id)
    if not db_creator_channel_info:
        db_creator_channel_info = bot.repos.creator_channels.get_info(db_temp_channel_info.creator_id)

    # Uses guild.get_member rather than bot.get_member to access nicknames
    owner = temp_channel.guild.get_member(db_temp_channel_info.owner_id) if db_temp_channel_info.owner_id else None
    guild_name = temp_channel.guild.name

    new_channel_name = db_creator_channel_info.child_name
    if "{user}" in str(new_channel_name):
        if owner:
            member_name = owner.nick if owner.nick else owner.display_name
        else:
            member_name = "Public"
            bot.logger.debug(
                f"Owner not found for temp channel {temp_channel.id} in guild '{guild_name}', using 'Public' for {{user}} placeholder."
            )
        new_channel_name = new_channel_name.replace("{user}", member_name)

    if "{activity}" in str(new_channel_name):
        activities = []
        for member in temp_channel.members:
            for activity in member.activities:
                if activity.type == discord.ActivityType.playing:
                    if activity.name.lower() not in (name.lower() for name in activities):
                        activities.append(activity.name)

        if len(activities) <= 0:
            activities.append("General")
        activities.sort(key=len)
        activity_text = ", ".join(activities)
        bot.logger.debug(
            f"Resolved {{activity}} placeholder for temp channel {temp_channel.id} in guild '{guild_name}': '{activity_text}'"
        )

        new_channel_name = new_channel_name.replace("{activity}", activity_text)

    if "{count}" in str(new_channel_name):
        count = db_temp_channel_info.number
        bot.logger.debug(
            f"Resolved {{count}} placeholder for temp channel {temp_channel.id} in guild '{guild_name}': {count}"
        )
        new_channel_name = new_channel_name.replace("{count}", str(count))

    # Max char is 100, using 98 just in case
    if len(str(new_channel_name)) > 95:
        bot.logger.debug(
            f"Truncating temp channel name for {temp_channel.id} in guild '{guild_name}' from {len(str(new_channel_name))} characters."
        )
        new_channel_name = new_channel_name[:95] + "..."

    return new_channel_name
