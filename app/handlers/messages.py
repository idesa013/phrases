from telebot import TeleBot

from app.config import ADMIN_IDS
from app.keyboards.inline import generate_only_keyboard
from app.keyboards.reply import (
    game_mode_keyboard,
    multi_game_keyboard,
    registration_keyboard,
)
from app.services.game_state import get_state
from app.services.stats_repository import (
    increment_right,
    increment_wrong,
    is_user_registered,
    register_user,
)
from app.utils.text import normalize_answer


MENU_BUTTONS = {
    "Register",
    "Single game",
    "Multi game",
    "Create",
    "Join",
    "Ended",
    "Back",
    "Start Game",
    "Cancel",
    "2",
    "3",
    "4",
    "5",
    "Admin-panel",
    "User List",
    "current statistic",
    "drop statistic",
}


def register_message_handlers(bot: TeleBot) -> None:
    @bot.message_handler(commands=["start", "help"])
    def handle_start(message) -> None:
        if not is_user_registered(message.from_user.id):
            bot.send_message(
                message.chat.id,
                "Для начала нужно пройти регистрацию.",
                reply_markup=registration_keyboard(),
            )
            return

        is_admin = message.from_user.id in ADMIN_IDS
        bot.send_message(
            message.chat.id,
            "Выбери режим игры.",
            reply_markup=game_mode_keyboard(is_admin=is_admin),
        )

    @bot.message_handler(func=lambda message: message.text == "Register")
    def handle_register(message) -> None:
        register_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            name=message.from_user.first_name,
            surname=message.from_user.last_name,
        )

        is_admin = message.from_user.id in ADMIN_IDS
        bot.send_message(
            message.chat.id,
            "Регистрация завершена.",
            reply_markup=game_mode_keyboard(is_admin=is_admin),
        )

    @bot.message_handler(func=lambda message: message.text == "Single game")
    def handle_single_game(message) -> None:
        if not is_user_registered(message.from_user.id):
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        bot.send_message(
            message.chat.id,
            "Нажми кнопку ниже, чтобы сгенерировать фразу.",
            reply_markup=generate_only_keyboard(),
        )

    @bot.message_handler(func=lambda message: message.text == "Multi game")
    def handle_multi_game(message) -> None:
        if not is_user_registered(message.from_user.id):
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        is_admin = message.from_user.id in ADMIN_IDS
        bot.send_message(
            message.chat.id,
            "Режим многопользовательской игры.\nВыбери действие:",
            reply_markup=multi_game_keyboard(is_admin=is_admin),
        )

    @bot.message_handler(func=lambda message: message.text == "Back")
    def handle_back(message) -> None:
        if not is_user_registered(message.from_user.id):
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        is_admin = message.from_user.id in ADMIN_IDS
        bot.send_message(
            message.chat.id,
            "Выбери режим игры.",
            reply_markup=game_mode_keyboard(is_admin=is_admin),
        )

    @bot.message_handler(
        func=lambda message: bool(message.text) and not message.text.startswith("/"),
        content_types=["text"],
    )
    def handle_answer(message) -> None:
        if message.text in MENU_BUTTONS:
            return

        if not is_user_registered(message.from_user.id):
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        state = get_state(message.from_user.id)

        if not state.waiting_for_answer or not state.phrase:
            is_admin = message.from_user.id in ADMIN_IDS
            bot.send_message(
                message.chat.id,
                "Выбери режим игры.",
                reply_markup=game_mode_keyboard(is_admin=is_admin),
            )
            return

        user_answer = normalize_answer(message.text or "")
        correct_answer = normalize_answer(state.phrase)
        image_message_id = state.image_message_id
        state.waiting_for_answer = False

        if image_message_id:
            try:
                bot.edit_message_reply_markup(
                    chat_id=message.chat.id,
                    message_id=image_message_id,
                    reply_markup=None,
                )
            except Exception:
                pass

        if user_answer == correct_answer:
            increment_right(message.from_user.id, message.from_user.username)
            bot.send_message(
                message.chat.id,
                f"✅ Отлично! Правильный ответ: {state.phrase}",
                reply_markup=generate_only_keyboard(),
            )
            return

        increment_wrong(message.from_user.id, message.from_user.username)
        bot.send_message(
            message.chat.id,
            f"❌ Неправильно.\nПравильный ответ: {state.phrase}",
            reply_markup=generate_only_keyboard(),
        )
