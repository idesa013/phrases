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


class MultiGame(BaseModel):
    id = AutoField()
    creator_user_id = IntegerField()
    creator_username = CharField(null=True)
    max_players = IntegerField()
    status = CharField(default="open")  # open, started, canceled, ended
    created_at = CharField(default=lambda: datetime.now().strftime("%Y%m%d:%H%M"))


class MultiGamePlayer(BaseModel):
    id = AutoField()
    game = ForeignKeyField(MultiGame, backref="players", on_delete="CASCADE")
    user_id = IntegerField()
    username = CharField(null=True)
    joined_at = CharField(default=lambda: datetime.now().strftime("%Y%m%d:%H%M"))


def init_multi_db() -> None:
    database.connect(reuse_if_open=True)
    database.create_tables([MultiGame, MultiGamePlayer])
    database.close()


def create_game(
    creator_user_id: int, creator_username: str | None, max_players: int
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

        result = []
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


def get_game(game_id: int) -> MultiGame | None:
    database.connect(reuse_if_open=True)
    try:
        return MultiGame.get_or_none(MultiGame.id == game_id)
    finally:
        database.close()


def get_game_participants(game_id: int) -> list[dict]:
    database.connect(reuse_if_open=True)
    try:
        players = (
            MultiGamePlayer.select()
            .where(MultiGamePlayer.game == game_id)
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
        return (
            MultiGamePlayer.get_or_none(
                (MultiGamePlayer.game == game_id) & (MultiGamePlayer.user_id == user_id)
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

        if MultiGamePlayer.get_or_none(
            (MultiGamePlayer.game == game) & (MultiGamePlayer.user_id == user_id)
        ):
            return False, "Ты уже в этой игре."

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
        if player:
            player.delete_instance()
            return True

        return False
    finally:
        database.close()
