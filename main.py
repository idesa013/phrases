from telebot import TeleBot
from telebot.types import BotCommand

from app.config import BOT_TOKEN
from app.handlers.admin import register_admin_handlers
from app.handlers.callbacks import register_callback_handlers
from app.handlers.game_menu import register_game_menu_handlers
from app.handlers.messages import register_message_handlers
from app.handlers.multi_callbacks import register_multi_callback_handlers
from app.handlers.multi_messages import register_multi_message_handlers
from app.handlers.statistics import register_statistics_handlers
from app.services.multi_repository import init_multi_db
from app.services.phrase_updater import update_phrases
from app.services.stats_repository import init_stats_db

bot = TeleBot(BOT_TOKEN, parse_mode="HTML")


def main() -> None:
    init_stats_db()
    init_multi_db()
    update_phrases(force=False)

    register_statistics_handlers(bot)
    register_admin_handlers(bot)

    register_game_menu_handlers(bot)
    register_multi_message_handlers(bot)
    register_multi_callback_handlers(bot)

    register_message_handlers(bot)
    register_callback_handlers(bot)

    bot.set_my_commands(
        [
            BotCommand("start", "Запустить бота"),
            BotCommand("statistics", "Показать статистику"),
        ]
    )

    bot.infinity_polling()


if __name__ == "__main__":
    main()
