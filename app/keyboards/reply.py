from telebot.types import KeyboardButton, ReplyKeyboardMarkup


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


def create_player_count_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        KeyboardButton("2"),
        KeyboardButton("3"),
        KeyboardButton("4"),
        KeyboardButton("5"),
    )
    keyboard.row(KeyboardButton("Back"))
    if is_admin:
        keyboard.row(KeyboardButton("Admin-panel"))
    return keyboard


def create_confirm_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        KeyboardButton("Start Game"),
        KeyboardButton("Back"),
    )
    if is_admin:
        keyboard.row(KeyboardButton("Admin-panel"))
    return keyboard


def join_confirm_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        KeyboardButton("Start Game"),
        KeyboardButton("Back"),
    )
    if is_admin:
        keyboard.row(KeyboardButton("Admin-panel"))
    return keyboard


def cancel_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(KeyboardButton("Cancel"))
    if is_admin:
        keyboard.row(KeyboardButton("Admin-panel"))
    return keyboard


def admin_main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        KeyboardButton("User List"),
        KeyboardButton("Back"),
    )
    return keyboard


def admin_user_actions_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        KeyboardButton("current statistic"),
        KeyboardButton("drop statistic"),
        KeyboardButton("multi statistic"),
        KeyboardButton("Back"),
    )
    return keyboard
