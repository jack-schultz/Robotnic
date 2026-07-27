# Sends Discord messages to log events for the bot itself
# Channel stored in settings.json
class BotLogService:
    def __init__(self, bot):
        self.bot = bot

        self.settings = self.bot.settings.get("notifications", {})
        channel_id = self.settings.get("channel_id")
        self.channel = self.bot.get_channel(channel_id)

    async def send(self, event: str, message="", embed=None):
        if not self.channel:
            return

        # Checks if logging the event is enabled in settings.json
        if not self.settings.get(event, False):
            return

        await self.channel.send(message, embed=embed)


# Sends Discord messages to log events relevant to a single guild for moderation purposes
# Channel stored in database
class GuildLogService:
    def __init__(self, bot):
        self.bot = bot

    async def send(self, event: str, guild, message="", embed=None):
        settings = self.bot.repos.guild_settings.get(guild.id)
        channel = self.bot.get_channel(settings["logs_channel_id"])
        if not channel:
            return

        # Checks if logging the event is enabled in database.db
        if not event in settings["enabled_log_events"]:
            return

        await channel.send(message, embed=embed)
