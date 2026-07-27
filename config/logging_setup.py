import logging
from datetime import datetime

from config.paths import LOG_DIR

logger = logging.getLogger(__name__)


def setup_logging(settings) -> None:
    if getattr(setup_logging, "_configured", False):
        return

    discord_debug = settings["debug"].get("discord", False)
    bot_debug = settings["debug"].get("bot", False)

    log_name = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(
        filename=LOG_DIR / f"{log_name}.log", encoding="utf-8", mode="w"
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(levelname)s:%(name)s: %(message)s")
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    app_level = logging.DEBUG if bot_debug else logging.INFO
    for package in ("bot", "cogs", "config", "database", "api"):
        logging.getLogger(package).setLevel(app_level)

    discord_level = logging.DEBUG if discord_debug else logging.INFO
    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(discord_level)

    logger.info("Bot logger initialized")
    logger.debug("Bot logger debug mode active")
    discord_logger.info("Discord logger initialized")
    discord_logger.debug("Discord logger debug mode active")

    setup_logging._configured = True
