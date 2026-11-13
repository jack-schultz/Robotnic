from pathlib import Path

ROOT = Path(__file__).parent.parent
LOG_DIR = ROOT / "logs"
STATS_LOG_PATH = LOG_DIR / "stats.csv"
ENV_PATH = ROOT / ".env"
SETTINGS_PATH = ROOT / "settings.json"
DEFAULT_SETTINGS_PATH = ROOT / "default_settings.json"
DB_PATH = ROOT / "database.db"
LOCALES_DIR = ROOT / "locales"
