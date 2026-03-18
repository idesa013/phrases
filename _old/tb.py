import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, CallbackContext, CallbackQueryHandler
from telegram import constants
from datetime import datetime
import os

# настроим модуль ведения журнала логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

async def start(update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("GENERATE phrase!", callback_data='y')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    user_first_name = update.effective_user.first_name
    if (update.effective_user.last_name):
        user_last_name = update.effective_user.last_name
    else:
        user_last_name = ''

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Привет <b>{user_first_name} {user_last_name}</b> !\n<b>Начнем игру?</b>',
        parse_mode=constants.ParseMode.HTML,
        reply_markup=reply_markup)


async def echo(update, context: CallbackContext) -> int:
    keyboard = [[InlineKeyboardButton("GENERATE phrase!", callback_data='y')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # if (counter == 0):
    query = update.callback_query
    await query.answer()

    from phr2 import phr

    phr = phr()

    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('phrase.jpg', 'rb'))

    await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"<b>{phr[1]}</b>"
            f"\n\nВведите свой ответ: <b>{phr[0]}</b>",
            parse_mode=constants.ParseMode.HTML,
            reply_markup=reply_markup
            )


if __name__ == '__main__':
    TOKEN = '6794514920:AAGBtizYGzMzkzhUmPbzh4-Dka4w5-0UcqY'
    application = ApplicationBuilder().token(TOKEN).build()

    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
  
    start_handler = CommandHandler('start', start)
    application.add_handler(CallbackQueryHandler(echo))
    application.add_handler(echo_handler)
    application.add_handler(start_handler)

    application.run_polling()