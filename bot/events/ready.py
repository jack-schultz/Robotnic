import logging
from bot.discord_audit import BotLogService, GuildLogService
from bot.tasks import background
from cogs.control_vc.views.control_view import refresh_control_messages

logger = logging.getLogger(__name__)


async def on_ready(bot):
    if bot.ready:
        await bot.BotLogService.send("reconnect", "Bot Reconnected")
        return

    # Set services that require channels to already be cached
    bot.BotLogService = BotLogService(bot)
    bot.GuildLogService = GuildLogService(bot)

    # Login notification
    logger.info(f"Logged in as {bot.user}")
    await bot.BotLogService.send(event="start", message=f"Bot {bot.user.mention} started.")

    # Start background tasks
    await background.create_tasks(bot)
    logger.info(f"Created background tasks")

    # Reconnect to control panels of existing temp channels
    await refresh_control_messages(bot)
    logger.info("Refreshed control messages")

    # Sync commands and notify
    await bot.sync_commands()
    logger.info(f'Commands synced')
    await bot.BotLogService.send(event="start", message=f"Commands synced.")

    bot.ready = True
