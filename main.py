from bot.bot import Bot
from config.bot_settings import load_settings
from bot.logging import setup_program_loggers
from config.env import load_tokens
import threading
from api.api import run_web


settings = load_settings()
logger = setup_program_loggers(settings)
bot_token, topgg_token = load_tokens(logger)

bot = Bot(
    token=bot_token,
    topgg_token=topgg_token,
    logger=logger,
    settings=settings,
)

threading.Thread(
    target=run_web,
    args=(settings["api"]["port"],),
    daemon=True,
).start()

bot.run()
