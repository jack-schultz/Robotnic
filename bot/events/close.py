import logging
from config.i18n import t

logger = logging.getLogger(__name__)


async def close(bot):
    logger.info(f'Logging out {bot.user}')

    if bot.BotLogService:
        await bot.BotLogService.send(event="stop", message=t("bot_log.stopping", mention=bot.user.mention))
