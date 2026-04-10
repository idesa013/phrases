from peewee import JOIN

from app.services.multi_repository import MultiGame, MultiGameStats
from app.services.stats_repository import User, UserStats, database


def list_users(limit: int = 100) -> list[dict]:
    database.connect(reuse_if_open=True)
    try:
        query = User.select().order_by(User.id.asc()).limit(limit)
        return [
            {
                "id": user.id,
                "user_id": user.user_id,
                "username": user.username,
                "name": user.name,
                "surname": user.surname,
                "reg_date": user.reg_date,
                "status": user.status,
            }
            for user in query
        ]
    finally:
        database.close()


def get_user_by_table_id(user_table_id: int) -> User | None:
    database.connect(reuse_if_open=True)
    try:
        return User.get_or_none(User.id == user_table_id)
    finally:
        database.close()


def get_user_stats_by_user_id(user_id: int) -> UserStats | None:
    database.connect(reuse_if_open=True)
    try:
        return UserStats.get_or_none(UserStats.user_id == user_id)
    finally:
        database.close()


def reset_user_stats_by_user_id(user_id: int) -> bool:
    database.connect(reuse_if_open=True)
    try:
        stats = UserStats.get_or_none(UserStats.user_id == user_id)
        if stats is None:
            return False

        stats.generated = 0
        stats.right = 0
        stats.wrong = 0
        stats.save()
        return True
    finally:
        database.close()


def get_multi_user_stats(user_id: int) -> dict[str, int]:
    database.connect(reuse_if_open=True)
    try:
        stats_rows = (
            MultiGameStats.select(MultiGameStats, MultiGame)
            .join(MultiGame, JOIN.INNER, on=(MultiGameStats.game_id == MultiGame.id))
            .where((MultiGameStats.user_id == user_id) & (MultiGame.status == "ended"))
            .order_by(MultiGameStats.game_id.asc())
        )

        total_games = 0
        win = 0
        second_place = 0
        third_place = 0
        fourth_place = 0
        lose = 0
        wrong = 0
        no_answer = 0

        for row in stats_rows:
            leaderboard = list(
                MultiGameStats.select()
                .where(MultiGameStats.game_id == row.game_id)
                .order_by(
                    MultiGameStats.right.desc(),
                    MultiGameStats.wrong.asc(),
                    MultiGameStats.username.asc(),
                )
            )

            if not leaderboard:
                continue

            players_count = len(leaderboard)
            place = None

            for index, item in enumerate(leaderboard, start=1):
                if item.user_id == user_id:
                    place = index
                    break

            if place is None:
                continue

            total_games += 1

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

            wrong += row.wrong
            no_answer += max(0, row.generated - row.right - row.wrong)

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
    finally:
        database.close()
