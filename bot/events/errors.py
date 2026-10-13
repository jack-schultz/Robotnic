import logging
import discord
from config.i18n import t

logger = logging.getLogger(__name__)


async def on_application_command_error(self, ctx, exception):
    lang = self.repos.guild_settings.get_language(ctx.guild_id)
    if isinstance(exception.original, discord.Forbidden):
        await ctx.send(t("errors.missing_permissions", lang))
    else:
        logger.error(f"ERROR in {__name__}\nContext: {ctx}\nException: {exception}")
        await ctx.send(t("errors.generic", lang))
