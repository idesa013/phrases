import logging
import threading
import time

from telebot import TeleBot
from telebot.types import BotCommand

from app.config import BOT_TOKEN, UPDATE_INTERVAL_SECONDS
from app.handlers.admin import register_admin_handlers
from app.handlers.callbacks import register_callback_handlers
from app.handlers.game_menu import register_game_menu_handlers
from app.handlers.messages import register_message_handlers
from app.handlers.multi_callbacks import register_multi_callback_handlers
from app.handlers.multi_gameplay import register_multi_gameplay_handlers
from app.handlers.multi_messages import register_multi_message_handlers
from app.handlers.statistics import register_statistics_handlers
from app.services.multi_repository import init_multi_db
from app.services.phrase_updater import update_phrases
from app.services.stats_repository import init_stats_db

bot = TeleBot(BOT_TOKEN, parse_mode="HTML")
logger = logging.getLogger(__name__)


def _run_daily_phrase_updates() -> None:
    while True:
        time.sleep(UPDATE_INTERVAL_SECONDS)
        try:
            result = update_phrases(force=False)
            logger.info("Плановое обновление фраз: %s", result)
        except Exception:
            logger.exception("Ошибка планового обновления фраз")


def _start_update_scheduler() -> None:
    thread = threading.Thread(
        target=_run_daily_phrase_updates,
        daemon=True,
        name="phrase-updater",
    )
    thread.start()


def main() -> None:
    init_stats_db()
    init_multi_db()
    update_phrases(force=False)
    _start_update_scheduler()

    register_statistics_handlers(bot)
    register_admin_handlers(bot)
    register_game_menu_handlers(bot)
    register_multi_message_handlers(bot)
    register_multi_callback_handlers(bot)
    register_multi_gameplay_handlers(bot)
    register_message_handlers(bot)
    register_callback_handlers(bot)

    bot.set_my_commands(
        [
            BotCommand("start", "Запустить бота"),
            BotCommand("statistics", "Показать статистику"),
            BotCommand("multi_statistics", "Показать мульти-статистику"),
        ]
    )

    bot.infinity_polling()


if __name__ == "__main__":
    main()
