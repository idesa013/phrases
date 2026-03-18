from telebot import TeleBot

from app.keyboards.inline import generate_only_keyboard
from app.services.game_state import get_state
from app.utils.text import normalize_phrase_text


def register_message_handlers(bot: TeleBot) -> None:
    @bot.message_handler(commands=["start", "help"])
    def handle_start(message) -> None:
        bot.send_message(
            message.chat.id,
            "Нажми кнопку ниже, чтобы сгенерировать фразу.",
            reply_markup=generate_only_keyboard(),
        )

    @bot.message_handler(func=lambda message: True, content_types=["text"])
    def handle_answer(message) -> None:
        state = get_state(message.from_user.id)

        if not state.waiting_for_answer or not state.phrase:
            bot.send_message(
                message.chat.id,
                "Нажми кнопку ниже, чтобы сгенерировать фразу.",
                reply_markup=generate_only_keyboard(),
            )
            return

        user_answer = normalize_phrase_text(message.text).casefold()
        correct_answer = normalize_phrase_text(state.phrase).casefold()

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
            bot.send_message(
                message.chat.id,
                f"✅ Отлично! Правильный ответ: <b>{state.phrase}</b>",
                reply_markup=generate_only_keyboard(),
            )
            return

        bot.send_message(
            message.chat.id,
            f"❌ Неправильно.\nПравильный ответ: <b>{state.phrase}</b>",
            reply_markup=generate_only_keyboard(),
        )
