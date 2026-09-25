import logging
import discord
from cogs.manage_vcs.owner_prefix import strip_owner_prefix

logger = logging.getLogger(__name__)


def create_temp_channel_name(bot, temp_channel, db_temp_channel_info=None, db_creator_channel_info=None):
    if not temp_channel:
        logger.debug("Skipping temp channel name generation: temp_channel is None.")
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
            member_name = strip_owner_prefix(bot, temp_channel.guild.id, member_name)
        else:
            member_name = "Public"
            logger.debug(
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
        logger.debug(
            f"Resolved {{activity}} placeholder for temp channel {temp_channel.id} in guild '{guild_name}': '{activity_text}'"
        )

        new_channel_name = new_channel_name.replace("{activity}", activity_text)

    if "{count}" in str(new_channel_name):
        count = db_temp_channel_info.number
        logger.debug(
            f"Resolved {{count}} placeholder for temp channel {temp_channel.id} in guild '{guild_name}': {count}"
        )
        new_channel_name = new_channel_name.replace("{count}", str(count))

    # If { is left, there must be another placeholder
    if "{" in new_channel_name:
        custom_placeholders = bot.repos.placeholders.get_all(temp_channel.guild.id)
        # Example for custom_placeholders
        # [{'id': 1, 'placeholder': '{region}', 'replace_text': 'EU', 'role_id': 932045374594621460}, {'id': 2, 'placeholder': '{region}', 'replace_text': 'AU', 'role_id': 932045364566040626}]

        if len(custom_placeholders) > 0:
            logger.debug(f"custom placeholders found for {temp_channel.name} ({temp_channel.id}) in '{guild_name}': {custom_placeholders}")

            owner_role_ids = [role.id for role in owner.roles]

            # Run through all placeholders checking for it in the name scheme and if owner has role
            for custom_placeholder in custom_placeholders:
                if not custom_placeholder["placeholder"] in new_channel_name:
                    continue
                if not custom_placeholder["role_id"] in owner_role_ids:
                    continue

                new_channel_name = new_channel_name.replace(custom_placeholder["placeholder"], str(custom_placeholder["replace_text"]))

        # Checks if there is still a placeholder left. If so, replace it with "".
        if "{" in new_channel_name:
            for custom_placeholder in custom_placeholders:
                if not custom_placeholder["placeholder"] in new_channel_name:
                    continue

                new_channel_name = new_channel_name.replace(custom_placeholder["placeholder"], str(""))

    # Max char is 100, using 98 just in case
    if len(str(new_channel_name)) > 95:
        logger.debug(
            f"Truncating temp channel name for {temp_channel.id} in guild '{guild_name}' from {len(str(new_channel_name))} characters."
        )
        new_channel_name = new_channel_name[:95] + "..."

    return new_channel_name
