from bot.bot import Bot
from config.bot_settings import load_settings
from config.logging_setup import setup_logging
from config.env import load_tokens
import threading
from api.api import run_web


settings = load_settings()
setup_logging(settings)
bot_token, topgg_token = load_tokens()

bot = Bot(
    token=bot_token,
    topgg_token=topgg_token,
    settings=settings,
)

threading.Thread(
    target=run_web,
    args=(settings["api"]["port"],),
    daemon=True,
).start()

bot.run()
