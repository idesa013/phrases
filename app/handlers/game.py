from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.keyboards.main import start_keyboard
from app.services.image_generator import render_phrase_image
from app.services.phrase_repository import get_random_phrase
from app.utils.text import normalize_answer


CURRENT_PHRASE_KEY = "current_phrase"


async def generate_phrase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.callback_query:
        await update.callback_query.answer()

    phrase = get_random_phrase()
    image_path, hint = render_phrase_image(phrase)
    context.user_data[CURRENT_PHRASE_KEY] = phrase

    with open(image_path, "rb") as image_file:
        await update.effective_chat.send_photo(photo=image_file)

    await update.effective_chat.send_message(
        text=f"<b>{hint}</b>\n\nВведите свой ответ:",
        parse_mode=ParseMode.HTML,
        reply_markup=start_keyboard(),
    )


async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    expected = context.user_data.get(CURRENT_PHRASE_KEY)
    if not expected:
        await update.effective_chat.send_message(
            text="Сначала нажми <b>GENERATE phrase!</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=start_keyboard(),
        )
        return

    user_answer = normalize_answer(update.message.text or "")
    correct_answer = normalize_answer(expected)

    if user_answer == correct_answer:
        context.user_data.pop(CURRENT_PHRASE_KEY, None)
        await update.effective_chat.send_message(
            text=f"✅ Верно!\n<b>{expected}</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=start_keyboard(),
        )
        return

    await update.effective_chat.send_message(
        text=(
            "❌ Неверно.\n"
            "Попробуй ещё раз или нажми <b>GENERATE phrase!</b> для новой фразы."
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=start_keyboard(),
    )
