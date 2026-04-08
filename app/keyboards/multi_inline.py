from math import ceil

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup


def open_games_keyboard(
    games: list[dict],
    page: int,
    total_games: int,
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=3)

    buttons = [
        InlineKeyboardButton(
            text=(
                f"{game['creator_username']} "
                f"{game['joined_count']}/{game['max_players']}"
            ),
            callback_data=f"join_game_select:{game['id']}",
        )
        for game in games
    ]

    for index in range(0, len(buttons), 3):
        keyboard.row(*buttons[index : index + 3])

    total_pages = max(1, ceil(total_games / 15))

    nav_buttons = []

    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton("⬅️", callback_data=f"games_page:{page - 1}")
        )

    nav_buttons.append(
        InlineKeyboardButton(f"{page}/{total_pages}", callback_data="games_page:stay")
    )

    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton("➡️", callback_data=f"games_page:{page + 1}")
        )

    keyboard.row(*nav_buttons)

    return keyboard
