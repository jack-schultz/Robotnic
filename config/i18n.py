import json
import logging
from discord.commands.core import valid_locales, validate_chat_input_name
from discord.utils import MISSING
from config.paths import LOCALES_DIR

logger = logging.getLogger(__name__)

DEFAULT_LANGUAGE = "en"


# Loads every locales/<code>.json file, keyed by language code
def _load_locales() -> dict[str, dict[str, str]]:
    locales = {}
    for path in sorted(LOCALES_DIR.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            locales[path.stem] = json.load(f)
    if DEFAULT_LANGUAGE not in locales:
        raise FileNotFoundError(f"Default locale file {DEFAULT_LANGUAGE}.json not found in {LOCALES_DIR}")
    return locales


# Maps Discord locale codes (e.g. "en-GB", "de") to the language code of the locale file that covers them
# Each locale file lists the Discord locales it covers under "_language.discord_locales"
def _map_discord_locales(locales) -> dict[str, str]:
    discord_locales = {}
    for code, strings in locales.items():
        for discord_locale in strings.get("_language.discord_locales", []):
            if discord_locale not in valid_locales:
                raise ValueError(f"Locale file {code}.json lists '{discord_locale}', which is not a valid Discord locale")
            if discord_locale in discord_locales:
                raise ValueError(f"Discord locale '{discord_locale}' is listed by both {discord_locales[discord_locale]}.json and {code}.json")
            discord_locales[discord_locale] = code
    return discord_locales


_locales = _load_locales()
_discord_locales = _map_discord_locales(_locales)


def available_languages() -> dict[str, str]:
    """Returns {language code: language name} for every loaded locale."""
    return {code: strings.get("_language.name", code) for code, strings in _locales.items()}


def language_from_discord_locale(discord_locale: str | None) -> str:
    """Returns the language code covering a Discord locale (e.g. a guild's preferred_locale), else the default language."""
    return _discord_locales.get(str(discord_locale), DEFAULT_LANGUAGE)


def localizations(key: str, **kwargs):
    """
    Returns {Discord locale: string} for every non-default language that has `key`.
    Used for Discord's built-in command localisations (name_localizations, description_localizations),
    which Discord shows based on each user's client language. The default language is the base name/description.
    Returns MISSING when there are none so py-cord omits the field.
    """
    result = {}
    for discord_locale, language in _discord_locales.items():
        if language == DEFAULT_LANGUAGE or key not in _locales[language]:
            continue
        result[discord_locale] = t(key, language, **kwargs)
    return result or MISSING


def name_localizations(key: str):
    """
    localizations() for slash command, group and option names, validated against Discord's naming rules
    (lowercase, no spaces, max 32 characters) so a bad translation fails on startup rather than on sync.
    """
    result = localizations(key)
    if result is not MISSING:
        for discord_locale, name in result.items():
            validate_chat_input_name(name, locale=discord_locale)
    return result


def command_kwargs(key: str) -> dict:
    """
    name, description and their localizations for a slash command, group or option, from `key`.name and `key`.description.
    Usage: @discord.slash_command(**command_kwargs("commands.ping"))
    """
    return {
        "name": t(f"{key}.name"),
        "name_localizations": name_localizations(f"{key}.name"),
        "description": t(f"{key}.description"),
        "description_localizations": localizations(f"{key}.description"),
    }


def command_text(*keys: str, language: str | None = None) -> str:
    """
    Command as typed, e.g. command_text("commands.settings", "commands.settings.controls") -> "/settings controls".
    For showing command names in messages in the guild's language.
    """
    return "/" + " ".join(t(f"{key}.name", language) for key in keys)


def t(key: str, language: str | None = None, /, **kwargs) -> str:
    """
    Returns the string for `key` in `language`, formatted with kwargs.
    Falls back to the default language if the language or key is missing, then to the key itself.
    Literal braces in locale strings must be escaped as {{ and }}.
    """
    if language not in _locales:
        language = DEFAULT_LANGUAGE

    text = _locales[language].get(key)
    if text is None and language != DEFAULT_LANGUAGE:
        logger.debug(f"Missing '{key}' in locale '{language}', falling back to '{DEFAULT_LANGUAGE}'")
        language = DEFAULT_LANGUAGE
        text = _locales[language].get(key)
    if text is None:
        logger.warning(f"Missing locale string '{key}'")
        return key

    try:
        return text.format(**kwargs)
    except (KeyError, IndexError, ValueError) as e:
        logger.warning(f"Failed to format locale string '{key}' in '{language}': {e}")
        if language != DEFAULT_LANGUAGE:
            return t(key, DEFAULT_LANGUAGE, **kwargs)
        return text
