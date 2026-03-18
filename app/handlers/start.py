from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.keyboards.main import start_keyboard


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    full_name = " ".join(part for part in [user.first_name or "", user.last_name or ""] if part).strip()

    await update.effective_chat.send_message(
        text=f"Привет <b>{full_name}</b>!\n<b>Начнем игру?</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=start_keyboard(),
    )
