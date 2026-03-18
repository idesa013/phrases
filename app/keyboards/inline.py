from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup


def phrase_image_keyboard_locked() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("GENERATE phrase!", callback_data="generate_phrase"),
        InlineKeyboardButton("Show Answer (5s)", callback_data="show_answer_locked"),
    )
    return keyboard


def phrase_image_keyboard_active() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("GENERATE phrase!", callback_data="generate_phrase"),
        InlineKeyboardButton("Show Answer", callback_data="show_answer"),
    )
    return keyboard


def generate_only_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("GENERATE phrase!", callback_data="generate_phrase"),
    )
    return keyboard
