from peewee import AutoField, CharField, IntegerField, Model, SqliteDatabase

from app.config import DB_PATH


database = SqliteDatabase(DB_PATH)


class BaseModel(Model):
    class Meta:
        database = database


class UserStats(BaseModel):
    id = AutoField()
    user_id = IntegerField(unique=True)
    username = CharField(null=True)
    generated = IntegerField(default=0)
    right = IntegerField(default=0)
    wrong = IntegerField(default=0)


def init_stats_db() -> None:
    database.connect(reuse_if_open=True)
    database.create_tables([UserStats])
    database.close()


def increment_generated(user_id: int, username: str | None) -> None:
    database.connect(reuse_if_open=True)

    user, created = UserStats.get_or_create(
        user_id=user_id,
        defaults={
            "username": username,
            "generated": 0,
            "right": 0,
            "wrong": 0,
        },
    )

    if not created:
        user.username = username

    user.generated += 1
    user.save()

    database.close()


def increment_right(user_id: int, username: str | None) -> None:
    database.connect(reuse_if_open=True)

    user, created = UserStats.get_or_create(
        user_id=user_id,
        defaults={
            "username": username,
            "generated": 0,
            "right": 0,
            "wrong": 0,
        },
    )

    if not created:
        user.username = username

    user.right += 1
    user.save()

    database.close()


def increment_wrong(user_id: int, username: str | None) -> None:
    database.connect(reuse_if_open=True)

    user, created = UserStats.get_or_create(
        user_id=user_id,
        defaults={
            "username": username,
            "generated": 0,
            "right": 0,
            "wrong": 0,
        },
    )

    if not created:
        user.username = username

    user.wrong += 1
    user.save()

    database.close()
