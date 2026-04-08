from telebot import TeleBot

from app.config import ADMIN_IDS
from app.keyboards.game_reply import root_game_keyboard, multi_game_keyboard
from app.keyboards.inline import generate_only_keyboard
from app.services.multi_state import reset_multi_state


def register_game_menu_handlers(bot: TeleBot) -> None:
    @bot.message_handler(commands=["start", "help"])
    def handle_start(message) -> None:
        is_admin = message.from_user.id in ADMIN_IDS
        reset_multi_state(message.from_user.id)
        bot.send_message(
            message.chat.id,
            "Выберите режим игры.",
            reply_markup=root_game_keyboard(is_admin=is_admin),
        )

    @bot.message_handler(func=lambda message: message.text == "Single game")
    def handle_single_game(message) -> None:
        bot.send_message(
            message.chat.id,
            "Нажми кнопку ниже, чтобы сгенерировать фразу.",
            reply_markup=generate_only_keyboard(),
        )

    @bot.message_handler(func=lambda message: message.text == "Multi game")
    def handle_multi_game(message) -> None:
        is_admin = message.from_user.id in ADMIN_IDS
        reset_multi_state(message.from_user.id)
        bot.send_message(
            message.chat.id,
            "Выбери действие.",
            reply_markup=multi_game_keyboard(is_admin=is_admin),
        )
