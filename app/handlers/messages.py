from telebot import TeleBot

from app.config import ADMIN_IDS
from app.keyboards.inline import generate_only_keyboard
from app.keyboards.reply import admin_entry_keyboard
from app.services.game_state import get_state
from app.utils.text import normalize_answer
from app.services.stats_repository import (
    increment_right,
    increment_wrong,
)


def register_message_handlers(bot: TeleBot) -> None:
    @bot.message_handler(commands=["start", "help"])
    def handle_start(message) -> None:
        if message.from_user.id in ADMIN_IDS:
            bot.send_message(
                message.chat.id,
                "Админ-доступ активен.",
                reply_markup=admin_entry_keyboard(),
            )

        bot.send_message(
            message.chat.id,
            "Нажми кнопку ниже, чтобы сгенерировать фразу.",
            reply_markup=generate_only_keyboard(),
        )

    @bot.message_handler(
        func=lambda message: bool(message.text) and not message.text.startswith("/"),
        content_types=["text"],
    )
    def handle_answer(message) -> None:
        state = get_state(message.from_user.id)

        if not state.waiting_for_answer or not state.phrase:
            bot.send_message(
                message.chat.id,
                "Нажми кнопку ниже, чтобы сгенерировать фразу.",
                reply_markup=generate_only_keyboard(),
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
