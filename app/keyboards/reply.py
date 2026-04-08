from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def game_mode_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        KeyboardButton("Single game"),
        KeyboardButton("Multi game"),
    )

    if is_admin:
        keyboard.row(KeyboardButton("Админ-панель"))

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
        keyboard.row(KeyboardButton("Админ-панель"))

    return keyboard


def admin_entry_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Админ-панель"))
    return keyboard


def admin_main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        KeyboardButton("Список пользователей"),
        KeyboardButton("Назад"),
    )
    return keyboard


def admin_user_actions_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        KeyboardButton("current statistic"),
        KeyboardButton("drop statistic"),
        KeyboardButton("Назад"),
    )
    return keyboard
