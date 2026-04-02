from telebot.types import ReplyKeyboardMarkup, KeyboardButton


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
