from datetime import datetime

from peewee import (
    AutoField,
    CharField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
)

from app.config import DB_PATH

database = SqliteDatabase(DB_PATH)


class BaseModel(Model):
    class Meta:
        database = database


class MultiConfig(BaseModel):
    id = AutoField()
    key = CharField(unique=True)
    value = IntegerField()


class MultiGame(BaseModel):
    id = AutoField()
    creator_user_id = IntegerField()
    creator_username = CharField(null=True)
    max_players = IntegerField()
    status = CharField(default="open")
    created_at = CharField(default=lambda: datetime.now().strftime("%Y%m%d:%H%M"))


class MultiGamePlayer(BaseModel):
    id = AutoField()
    game = ForeignKeyField(MultiGame, backref="players", on_delete="CASCADE")
    user_id = IntegerField()
    username = CharField(null=True)
    joined_at = CharField(default=lambda: datetime.now().strftime("%Y%m%d:%H%M"))


class MultiGameStats(BaseModel):
    id = AutoField()
    game_id = IntegerField()
    user_id = IntegerField()
    username = CharField(null=True)
    generated = IntegerField(default=0)
    right = IntegerField(default=0)
    wrong = IntegerField(default=0)


def init_multi_db() -> None:
    database.connect(reuse_if_open=True)
    try:
        database.create_tables(
            [MultiConfig, MultiGame, MultiGamePlayer, MultiGameStats]
        )

        MultiConfig.get_or_create(key="start_delay_seconds", defaults={"value": 5})
        MultiConfig.get_or_create(key="answer_time_seconds", defaults={"value": 10})
        MultiConfig.get_or_create(key="answer_attempts", defaults={"value": 2})
        MultiConfig.get_or_create(key="next_round_delay_seconds", defaults={"value": 5})
        MultiConfig.get_or_create(key="rounds_count", defaults={"value": 5})
    finally:
        database.close()


def _get_config_int(key: str, default: int) -> int:
    database.connect(reuse_if_open=True)
    try:
        config = MultiConfig.get_or_none(MultiConfig.key == key)
        if config is None:
            config = MultiConfig.create(key=key, value=default)
        return int(config.value)
    finally:
        database.close()


def get_start_delay_seconds() -> int:
    return _get_config_int("start_delay_seconds", 5)


def get_answer_time_seconds() -> int:
    return _get_config_int("answer_time_seconds", 10)


def get_answer_attempts() -> int:
    return _get_config_int("answer_attempts", 2)


def get_next_round_delay_seconds() -> int:
    return _get_config_int("next_round_delay_seconds", 5)


def get_rounds_count() -> int:
    return _get_config_int("rounds_count", 5)


def create_game(
    creator_user_id: int,
    creator_username: str | None,
    max_players: int,
) -> MultiGame:
    database.connect(reuse_if_open=True)
    try:
        game = MultiGame.create(
            creator_user_id=creator_user_id,
            creator_username=creator_username,
            max_players=max_players,
            status="open",
        )

        MultiGamePlayer.create(
            game=game,
            user_id=creator_user_id,
            username=creator_username,
        )

        return game
    finally:
        database.close()


def list_open_games(limit: int = 15, offset: int = 0) -> list[dict]:
    database.connect(reuse_if_open=True)
    try:
        games = (
            MultiGame.select()
            .where(MultiGame.status == "open")
            .order_by(MultiGame.id.desc())
            .limit(limit)
            .offset(offset)
        )

        result: list[dict] = []

        for game in games:
            joined_count = (
                MultiGamePlayer.select().where(MultiGamePlayer.game == game).count()
            )

            result.append(
                {
                    "id": game.id,
                    "creator_user_id": game.creator_user_id,
                    "creator_username": game.creator_username or "unknown",
                    "max_players": game.max_players,
                    "joined_count": joined_count,
                }
            )

        return result
    finally:
        database.close()


def count_open_games() -> int:
    database.connect(reuse_if_open=True)
    try:
        return MultiGame.select().where(MultiGame.status == "open").count()
    finally:
        database.close()


def list_user_ended_games(user_id: int, limit: int = 15, offset: int = 0) -> list[dict]:
    database.connect(reuse_if_open=True)
    try:
        query = (
            MultiGame.select(MultiGame)
            .join(MultiGamePlayer, on=(MultiGamePlayer.game == MultiGame.id))
            .where((MultiGame.status == "ended") & (MultiGamePlayer.user_id == user_id))
            .order_by(MultiGame.id.desc())
            .limit(limit)
            .offset(offset)
        )

        result: list[dict] = []
        seen_ids: set[int] = set()

        for game in query:
            if game.id in seen_ids:
                continue
            seen_ids.add(game.id)
            result.append(
                {
                    "id": game.id,
                    "creator_user_id": game.creator_user_id,
                    "creator_username": game.creator_username or "unknown",
                    "status": game.status,
                    "created_at": game.created_at,
                }
            )

        return result
    finally:
        database.close()


def count_user_ended_games(user_id: int) -> int:
    database.connect(reuse_if_open=True)
    try:
        query = (
            MultiGame.select(MultiGame.id)
            .join(MultiGamePlayer, on=(MultiGamePlayer.game == MultiGame.id))
            .where((MultiGame.status == "ended") & (MultiGamePlayer.user_id == user_id))
            .distinct()
        )
        return query.count()
    finally:
        database.close()


def get_game(game_id: int) -> MultiGame | None:
    database.connect(reuse_if_open=True)
    try:
        return MultiGame.get_or_none(MultiGame.id == game_id)
    finally:
        database.close()


def set_game_status(game_id: int, status: str) -> None:
    database.connect(reuse_if_open=True)
    try:
        game = MultiGame.get_or_none(MultiGame.id == game_id)
        if game is None:
            return
        game.status = status
        game.save()
    finally:
        database.close()


def get_game_participants(game_id: int) -> list[dict]:
    database.connect(reuse_if_open=True)
    try:
        game = MultiGame.get_or_none(MultiGame.id == game_id)
        if game is None:
            return []

        players = (
            MultiGamePlayer.select()
            .where(MultiGamePlayer.game == game)
            .order_by(MultiGamePlayer.id.asc())
        )

        return [
            {
                "user_id": player.user_id,
                "username": player.username,
            }
            for player in players
        ]
    finally:
        database.close()


def is_user_in_game(game_id: int, user_id: int) -> bool:
    database.connect(reuse_if_open=True)
    try:
        game = MultiGame.get_or_none(MultiGame.id == game_id)
        if game is None:
            return False

        return (
            MultiGamePlayer.get_or_none(
                (MultiGamePlayer.game == game) & (MultiGamePlayer.user_id == user_id)
            )
            is not None
        )
    finally:
        database.close()


def join_game(game_id: int, user_id: int, username: str | None) -> tuple[bool, str]:
    database.connect(reuse_if_open=True)
    try:
        game = MultiGame.get_or_none(MultiGame.id == game_id)
        if game is None:
            return False, "Игра не найдена."

        if game.status != "open":
            return False, "Игра уже недоступна."

        existing_player = MultiGamePlayer.get_or_none(
            (MultiGamePlayer.game == game) & (MultiGamePlayer.user_id == user_id)
        )
        if existing_player is not None:
            return False, "Ты уже присоединился к этой игре."

        joined_count = (
            MultiGamePlayer.select().where(MultiGamePlayer.game == game).count()
        )

        if joined_count >= game.max_players:
            return False, "В игре уже нет свободных мест."

        MultiGamePlayer.create(
            game=game,
            user_id=user_id,
            username=username,
        )

        new_joined_count = (
            MultiGamePlayer.select().where(MultiGamePlayer.game == game).count()
        )

        if new_joined_count >= game.max_players:
            game.status = "ready"
            game.save()

        return True, "ok"
    finally:
        database.close()


def cancel_game(game_id: int, user_id: int) -> bool:
    database.connect(reuse_if_open=True)
    try:
        game = MultiGame.get_or_none(MultiGame.id == game_id)
        if game is None:
            return False

        if game.creator_user_id == user_id:
            game.status = "canceled"
            game.save()
            return True

        player = MultiGamePlayer.get_or_none(
            (MultiGamePlayer.game == game) & (MultiGamePlayer.user_id == user_id)
        )
        if player is None:
            return False

        player.delete_instance()

        current_count = (
            MultiGamePlayer.select().where(MultiGamePlayer.game == game).count()
        )

        if current_count < game.max_players and game.status == "ready":
            game.status = "open"
            game.save()

        return True
    finally:
        database.close()


def clear_game_players(game_id: int) -> None:
    database.connect(reuse_if_open=True)
    try:
        game = MultiGame.get_or_none(MultiGame.id == game_id)
        if game is None:
            return

        (MultiGamePlayer.delete().where(MultiGamePlayer.game == game).execute())
    finally:
        database.close()


def remove_game_player(game_id: int, user_id: int) -> None:
    database.connect(reuse_if_open=True)
    try:
        game = MultiGame.get_or_none(MultiGame.id == game_id)
        if game is None:
            return

        (
            MultiGamePlayer.delete()
            .where(
                (MultiGamePlayer.game == game) & (MultiGamePlayer.user_id == user_id)
            )
            .execute()
        )
    finally:
        database.close()


def init_round_stats(game_id: int, participants: list[dict]) -> None:
    database.connect(reuse_if_open=True)
    try:
        for participant in participants:
            stat, _ = MultiGameStats.get_or_create(
                game_id=game_id,
                user_id=participant["user_id"],
                defaults={
                    "username": participant["username"],
                    "generated": 0,
                    "right": 0,
                    "wrong": 0,
                },
            )
            stat.username = participant["username"]
            stat.generated += 1
            stat.save()
    finally:
        database.close()


def mark_game_forfeit(
    game_id: int,
    user_id: int,
    username: str | None,
    total_rounds: int,
) -> None:
    database.connect(reuse_if_open=True)
    try:
        stat, _ = MultiGameStats.get_or_create(
            game_id=game_id,
            user_id=user_id,
            defaults={
                "username": username,
                "generated": 0,
                "right": 0,
                "wrong": 0,
            },
        )
        stat.username = username
        stat.generated = total_rounds
        stat.right = 0
        stat.wrong = total_rounds
        stat.save()
    finally:
        database.close()


def increment_game_right(game_id: int, user_id: int, username: str | None) -> None:
    database.connect(reuse_if_open=True)
    try:
        stat, _ = MultiGameStats.get_or_create(
            game_id=game_id,
            user_id=user_id,
            defaults={
                "username": username,
                "generated": 0,
                "right": 0,
                "wrong": 0,
            },
        )
        stat.username = username
        stat.right += 1
        stat.save()
    finally:
        database.close()


def increment_game_wrong(game_id: int, user_id: int, username: str | None) -> None:
    database.connect(reuse_if_open=True)
    try:
        stat, _ = MultiGameStats.get_or_create(
            game_id=game_id,
            user_id=user_id,
            defaults={
                "username": username,
                "generated": 0,
                "right": 0,
                "wrong": 0,
            },
        )
        stat.username = username
        stat.wrong += 1
        stat.save()
    finally:
        database.close()


def get_game_leaderboard(game_id: int) -> list[dict]:
    database.connect(reuse_if_open=True)
    try:
        query = (
            MultiGameStats.select()
            .where(MultiGameStats.game_id == game_id)
            .order_by(
                MultiGameStats.right.desc(),
                MultiGameStats.wrong.asc(),
                MultiGameStats.username.asc(),
            )
        )

        return [
            {
                "user_id": item.user_id,
                "username": item.username,
                "generated": item.generated,
                "right": item.right,
                "wrong": item.wrong,
            }
            for item in query
        ]
    finally:
        database.close()
