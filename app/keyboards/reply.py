from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def registration_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(KeyboardButton("Register"))
    return keyboard


def game_mode_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        KeyboardButton("Single game"),
        KeyboardButton("Multi game"),
    )
    if is_admin:
        keyboard.row(KeyboardButton("Admin-panel"))
    return keyboard


def multi_game_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        KeyboardButton("Create"),
        KeyboardButton("Join"),
        KeyboardButton("Ended"),
        KeyboardButton("Back"),
    )
    if is_admin:
        keyboard.row(KeyboardButton("Admin-panel"))
    return keyboard


def admin_main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        KeyboardButton("User List"),
        KeyboardButton("Back"),
    )
    return keyboard


def admin_user_actions_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        KeyboardButton("current statistic"),
        KeyboardButton("drop statistic"),
        KeyboardButton("Back"),
    )
    return keyboard
