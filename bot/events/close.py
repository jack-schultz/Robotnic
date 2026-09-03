import logging

logger = logging.getLogger(__name__)


async def close(bot):
    logger.info(f'Logging out {bot.user}')

    if bot.BotLogService:
        await bot.BotLogService.send(event="stop", message=f"Bot {bot.user.mention} stopping.")
