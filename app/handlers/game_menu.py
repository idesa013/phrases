from telebot import TeleBot

from app.config import ADMIN_IDS
from app.keyboards.inline import generate_only_keyboard
from app.keyboards.reply import (
    game_mode_keyboard,
    multi_game_keyboard,
    registration_keyboard,
)
from app.services.menu_state import reset_menu_state, set_menu_state
from app.services.multi_state import reset_multi_state
from app.services.stats_repository import is_user_registered


def register_game_menu_handlers(bot: TeleBot) -> None:
    @bot.message_handler(commands=["start", "help"])
    def handle_start(message) -> None:
        reset_multi_state(message.from_user.id)
        reset_menu_state(message.from_user.id)

        if not is_user_registered(message.from_user.id):
            set_menu_state(message.from_user.id, "registration")
            bot.send_message(
                message.chat.id,
                "Для начала нужно пройти регистрацию.",
                reply_markup=registration_keyboard(),
            )
            return

        is_admin = message.from_user.id in ADMIN_IDS
        set_menu_state(message.from_user.id, "root")
        bot.send_message(
            message.chat.id,
            "Выбери режим игры.",
            reply_markup=game_mode_keyboard(is_admin=is_admin),
        )

    @bot.message_handler(func=lambda message: message.text == "Register")
    def handle_register(message) -> None:
        from app.services.stats_repository import register_user

        register_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            name=message.from_user.first_name,
            surname=message.from_user.last_name,
        )

        is_admin = message.from_user.id in ADMIN_IDS
        set_menu_state(message.from_user.id, "root")
        bot.send_message(
            message.chat.id,
            "Регистрация завершена.",
            reply_markup=game_mode_keyboard(is_admin=is_admin),
        )

    @bot.message_handler(func=lambda message: message.text == "Single game")
    def handle_single_game(message) -> None:
        if not is_user_registered(message.from_user.id):
            set_menu_state(message.from_user.id, "registration")
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        set_menu_state(message.from_user.id, "single_game")
        bot.send_message(
            message.chat.id,
            "Нажми кнопку ниже, чтобы сгенерировать фразу.",
            reply_markup=generate_only_keyboard(),
        )

    @bot.message_handler(func=lambda message: message.text == "Multi game")
    def handle_multi_game(message) -> None:
        if not is_user_registered(message.from_user.id):
            set_menu_state(message.from_user.id, "registration")
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        is_admin = message.from_user.id in ADMIN_IDS
        reset_multi_state(message.from_user.id)
        set_menu_state(message.from_user.id, "multi_menu")
        bot.send_message(
            message.chat.id,
            "Выбери действие.",
            reply_markup=multi_game_keyboard(is_admin=is_admin),
        )
