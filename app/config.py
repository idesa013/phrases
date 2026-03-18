from pathlib import Path
from dotenv import load_dotenv
import os


BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
DATA_DIR = APP_DIR / "data"
ASSETS_DIR = APP_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"

ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

PHRASES_PATH = DATA_DIR / "phrases.json"
SOURCES_PATH = DATA_DIR / "sources.json"
UPDATE_STATE_PATH = DATA_DIR / "update_state.json"

IMAGE_PATH = BASE_DIR / "phrase.jpg"

FONT_MAIN_PATH = FONTS_DIR / "ds_moster.ttf"
FONT_HINT_PATH = FONTS_DIR / "arial.ttf"
FONT_HINT_BOLD_PATH = FONTS_DIR / "arialbd.ttf"

WIKTIONARY_PAGE_TITLE = "Приложение:Список_фразеологизмов_русского_языка"
WIKTIONARY_API_URL = "https://ru.wiktionary.org/w/api.php"

HTTP_USER_AGENT = (
    "phrase-bot/1.0 " "(Telegram bot for phrase game; contact: youremail@example.com)"
)

WIKTIONARY_URL = (
    "https://ru.wiktionary.org/wiki/" "Приложение:Список_фразеологизмов_русского_языка"
)

UPDATE_INTERVAL_SECONDS = 60 * 60 * 24
REQUEST_TIMEOUT = 20
