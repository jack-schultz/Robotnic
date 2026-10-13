import logging
from config.i18n import t
from bot.discord_audit import BotLogService, GuildLogService
from bot.tasks import background
from cogs.control_vc.views.control_view import refresh_control_messages

logger = logging.getLogger(__name__)


async def on_ready(bot):
    if bot.ready:
        await bot.BotLogService.send("reconnect", t("bot_log.reconnected"))
        return

    # Set services that require channels to already be cached
    bot.BotLogService = BotLogService(bot)
    bot.GuildLogService = GuildLogService(bot)

    # Login notification
    logger.info(f"Logged in as {bot.user}")
    await bot.BotLogService.send(event="start", message=t("bot_log.started", mention=bot.user.mention))

    # Start background tasks
    await background.create_tasks(bot)
    logger.info(f"Created background tasks")

    # Reconnect to control panels of existing temp channels
    await refresh_control_messages(bot)
    logger.info("Refreshed control messages")

    # Sync commands and notify
    await bot.sync_commands()
    logger.info(f'Commands synced')
    await bot.BotLogService.send(event="start", message=t("bot_log.commands_synced"))

    bot.ready = True
