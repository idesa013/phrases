from telebot import TeleBot

from app.config import BOT_TOKEN
from app.handlers.callbacks import register_callback_handlers
from app.handlers.messages import register_message_handlers
from app.services.phrase_updater import update_phrases

bot = TeleBot(BOT_TOKEN, parse_mode="HTML")


def main() -> None:
    update_phrases(force=False)
    register_message_handlers(bot)
    register_callback_handlers(bot)
    bot.infinity_polling()


if __name__ == "__main__":
    main()
