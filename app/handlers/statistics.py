from telebot import TeleBot

from app.keyboards.inline import generate_only_keyboard
from app.services.multi_repository import (
    MultiGameStats,
    count_user_ended_games,
    database as multi_database,
    get_game_leaderboard,
    list_user_ended_games,
)
from app.services.statistics_image import render_statistics_chart
from app.services.stats_repository import get_user_stats


def get_multi_user_statistics(user_id: int) -> dict[str, int]:
    total_games = count_user_ended_games(user_id)

    ended_games = list_user_ended_games(
        user_id=user_id,
        limit=100000,
        offset=0,
    )

    win = 0
    second_place = 0
    third_place = 0
    fourth_place = 0
    lose = 0
    wrong = 0
    no_answer = 0

    multi_database.connect(reuse_if_open=True)
    try:
        for game in ended_games:
            game_id = game["id"]

            leaderboard = get_game_leaderboard(game_id)
            if not leaderboard:
                continue

            players_count = len(leaderboard)
            place = None

            for index, item in enumerate(leaderboard, start=1):
                if item["user_id"] == user_id:
                    place = index
                    break

            if place is None:
                continue

            stats_row = MultiGameStats.get_or_none(
                (MultiGameStats.game_id == game_id)
                & (MultiGameStats.user_id == user_id)
            )

            if stats_row is not None:
                wrong += stats_row.wrong
                no_answer += max(
                    0, stats_row.generated - stats_row.right - stats_row.wrong
                )

            if place == 1:
                win += 1
            if place == 2 and players_count > 2:
                second_place += 1
            if place == 3 and players_count > 3:
                third_place += 1
            if place == 4 and players_count > 4:
                fourth_place += 1
            if place == players_count:
                lose += 1
    finally:
        multi_database.close()

    return {
        "total_games": total_games,
        "win": win,
        "second_place": second_place,
        "third_place": third_place,
        "fourth_place": fourth_place,
        "lose": lose,
        "wrong": wrong,
        "no_answer": no_answer,
    }


def format_multi_statistics_text(stats: dict[str, int]) -> str:
    return (
        f"Total games: {stats['total_games']}\n"
        f"🥇 Win: {stats['win']}\n"
        f"🥈 Second place: {stats['second_place']}\n"
        f"🥉 Third place: {stats['third_place']}\n"
        f"🏅 Fourth place: {stats['fourth_place']}\n"
        f"❌ Lose: {stats['lose']}"
    )


def register_statistics_handlers(bot: TeleBot) -> None:
    @bot.message_handler(commands=["statistics"])
    def handle_statistics(message) -> None:
        try:
            stats = get_user_stats(message.from_user.id)

            chart_path = render_statistics_chart(
                user_id=message.from_user.id,
                username=message.from_user.username,
                generated=stats["generated"],
                right=stats["right"],
                wrong=stats["wrong"],
            )

            with open(chart_path, "rb") as photo:
                bot.send_photo(
                    chat_id=message.chat.id,
                    photo=photo,
                    reply_markup=generate_only_keyboard(),
                )
        except Exception as error:
            bot.send_message(
                message.chat.id,
                f"statistics error: {type(error).__name__}: {error}",
                reply_markup=generate_only_keyboard(),
            )
            raise

    @bot.message_handler(commands=["multi_statistics"])
    def handle_multi_statistics(message) -> None:
        try:
            stats = get_multi_user_statistics(message.from_user.id)

            bot.send_message(
                message.chat.id,
                format_multi_statistics_text(stats),
            )
        except Exception as error:
            bot.send_message(
                message.chat.id,
                f"multi_statistics error: {type(error).__name__}: {error}",
                reply_markup=generate_only_keyboard(),
            )
            raise
