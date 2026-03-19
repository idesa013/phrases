import threading
from time import time

from telebot import TeleBot

from app.keyboards.inline import (
    generate_only_keyboard,
    phrase_image_keyboard_active,
    phrase_image_keyboard_locked,
)
from app.services.game_state import get_state, mark_generated
from app.services.image_generator import render_phrase_image
from app.services.phrase_repository import get_random_phrase
from app.services.stats_repository import increment_generated


def activate_show_answer_button(bot: TeleBot, chat_id: int, message_id: int) -> None:
    try:
        bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=phrase_image_keyboard_active(),
        )
    except Exception:
        pass


def register_callback_handlers(bot: TeleBot) -> None:
    @bot.callback_query_handler(func=lambda call: call.data == "generate_phrase")
    def handle_generate_phrase(call) -> None:
        current_state = get_state(call.from_user.id)
        phrase = get_random_phrase(exclude=current_state.phrase)
        state = mark_generated(call.from_user.id, phrase)
        increment_generated(call.from_user.id, call.from_user.username)

        image_path = render_phrase_image(phrase)

        bot.answer_callback_query(call.id)

        with open(image_path, "rb") as photo:
            sent_message = bot.send_photo(
                chat_id=call.message.chat.id,
                photo=photo,
                reply_markup=phrase_image_keyboard_locked(),
            )

        state.image_message_id = sent_message.message_id

        timer = threading.Timer(
            5.0,
            activate_show_answer_button,
            args=(bot, sent_message.chat.id, sent_message.message_id),
        )
        timer.daemon = True
        timer.start()

    @bot.callback_query_handler(func=lambda call: call.data == "show_answer_locked")
    def handle_show_answer_locked(call) -> None:
        state = get_state(call.from_user.id)
        elapsed = time() - state.generated_at if state.generated_at else 0

        wait_seconds = max(1, int(5 - elapsed + 0.999)) if elapsed < 5 else 0

        if wait_seconds > 0:
            bot.answer_callback_query(
                call.id,
                text=f"Подожди ещё {wait_seconds} сек.",
                show_alert=False,
            )
            return

        try:
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=phrase_image_keyboard_active(),
            )
        except Exception:
            pass

        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "show_answer")
    def handle_show_answer(call) -> None:
        state = get_state(call.from_user.id)

        bot.answer_callback_query(call.id)

        if not state.phrase:
            bot.send_message(
                call.message.chat.id,
                "Сначала сгенерируй фразу.",
                reply_markup=generate_only_keyboard(),
            )
            return

        state.answer_shown = True
        state.waiting_for_answer = False

        if state.image_message_id:
            try:
                bot.edit_message_reply_markup(
                    chat_id=call.message.chat.id,
                    message_id=state.image_message_id,
                    reply_markup=None,
                )
            except Exception:
                pass

        bot.send_message(
            call.message.chat.id,
            f"Ответ: <b>{state.phrase}</b>",
            reply_markup=generate_only_keyboard(),
        )
