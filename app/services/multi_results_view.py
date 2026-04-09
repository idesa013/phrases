from telebot import TeleBot

from app.keyboards.reply import multi_game_keyboard
from app.services.multi_repository import get_game_leaderboard
from app.services.multi_statistics_image import render_multi_statistics_image


def _format_username(username: str | None) -> str:
    if username:
        return f"@{username}"
    return "без username"


def _detect_total_rounds(leaderboard: list[dict]) -> int:
    if not leaderboard:
        return 0
    return max(int(item.get("generated", 0)) for item in leaderboard)


def build_leaderboard_text(game_id: int, leaderboard: list[dict]) -> str:
    total_rounds = _detect_total_rounds(leaderboard)

    lines = [
        f"Игра № {game_id} окончена.",
        f"Всего заданий: {total_rounds}",
        "",
        "Статистика ответов игроков:",
    ]

    if not leaderboard:
        lines.append("Статистика пока отсутствует.")
        return "\n".join(lines)

    for index, item in enumerate(leaderboard, start=1):
        username = _format_username(item.get("username"))
        lines.append(
            f"{index}. {username} — "
            f"Правильных: {item.get('right', 0)}, "
            f"Неправильных: {item.get('wrong', 0)}"
        )

    return "\n".join(lines)


def send_game_results(
    bot: TeleBot,
    chat_id: int,
    game_id: int,
    is_admin: bool = False,
) -> None:
    leaderboard = get_game_leaderboard(game_id)
    total_rounds = _detect_total_rounds(leaderboard)
    text = build_leaderboard_text(game_id, leaderboard)

    image_path = render_multi_statistics_image(
        game_id=game_id,
        total_rounds=total_rounds,
        leaderboard=leaderboard,
    )

    with open(image_path, "rb") as photo:
        bot.send_photo(
            chat_id,
            photo,
            caption=text,
            reply_markup=multi_game_keyboard(is_admin=is_admin),
        )
