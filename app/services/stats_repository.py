from datetime import datetime

from peewee import AutoField, CharField, IntegerField, Model, SqliteDatabase, fn

from app.config import DB_PATH

database = SqliteDatabase(DB_PATH)


class BaseModel(Model):
    class Meta:
        database = database


class User(BaseModel):
    id = AutoField()
    user_id = IntegerField(unique=True)
    username = CharField(null=True)
    name = CharField(null=True)
    surname = CharField(null=True)
    reg_date = CharField()
    status = IntegerField(default=1)


class UserStats(BaseModel):
    id = AutoField()
    user_id = IntegerField(unique=True)
    username = CharField(null=True)
    generated = IntegerField(default=0)
    right = IntegerField(default=0)
    wrong = IntegerField(default=0)


def init_stats_db() -> None:
    database.connect(reuse_if_open=True)
    database.create_tables([User, UserStats])
    database.close()


def _now_reg_date() -> str:
    return datetime.now().strftime("%Y%m%d:%H%M")


def get_user(user_id: int) -> User | None:
    database.connect(reuse_if_open=True)
    try:
        return User.get_or_none(User.user_id == user_id)
    finally:
        database.close()


def get_registered_user_by_username(username: str) -> User | None:
    normalized_username = username.strip().lstrip("@").lower()
    if not normalized_username:
        return None

    database.connect(reuse_if_open=True)
    try:
        return User.get_or_none(
            (fn.LOWER(User.username) == normalized_username) & (User.status == 1)
        )
    finally:
        database.close()


def is_user_registered(user_id: int) -> bool:
    database.connect(reuse_if_open=True)
    try:
        user = User.get_or_none(User.user_id == user_id)
        return bool(user and user.status == 1)
    finally:
        database.close()


def register_user(
    user_id: int,
    username: str | None,
    name: str | None,
    surname: str | None,
) -> User:
    database.connect(reuse_if_open=True)
    try:
        user, created = User.get_or_create(
            user_id=user_id,
            defaults={
                "username": username,
                "name": name,
                "surname": surname,
                "reg_date": _now_reg_date(),
                "status": 1,
            },
        )

        if not created:
            user.username = username
            user.name = name
            user.surname = surname
            user.status = 1
            if not user.reg_date:
                user.reg_date = _now_reg_date()
            user.save()

        return user
    finally:
        database.close()


def increment_generated(user_id: int, username: str | None) -> None:
    database.connect(reuse_if_open=True)
    try:
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
    finally:
        database.close()


def increment_right(user_id: int, username: str | None) -> None:
    database.connect(reuse_if_open=True)
    try:
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
    finally:
        database.close()


def increment_wrong(user_id: int, username: str | None) -> None:
    database.connect(reuse_if_open=True)
    try:
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
    finally:
        database.close()


def get_user_stats(user_id: int) -> dict:
    database.connect(reuse_if_open=True)
    try:
        user = UserStats.get_or_none(UserStats.user_id == user_id)
        if user is None:
            return {
                "generated": 0,
                "right": 0,
                "wrong": 0,
            }
        return {
            "generated": user.generated,
            "right": user.right,
            "wrong": user.wrong,
        }
    finally:
        database.close()


def get_user_by_stats_id(stats_id: int) -> UserStats | None:
    database.connect(reuse_if_open=True)
    try:
        return UserStats.get_or_none(UserStats.id == stats_id)
    finally:
        database.close()


def list_users_stats(limit: int = 50) -> list[dict]:
    database.connect(reuse_if_open=True)
    try:
        query = UserStats.select().order_by(UserStats.id.asc()).limit(limit)
        return [
            {
                "id": user.id,
                "user_id": user.user_id,
                "username": user.username,
                "generated": user.generated,
                "right": user.right,
                "wrong": user.wrong,
            }
            for user in query
        ]
    finally:
        database.close()


def reset_user_stats_by_stats_id(stats_id: int) -> bool:
    database.connect(reuse_if_open=True)
    try:
        user = UserStats.get_or_none(UserStats.id == stats_id)
        if user is None:
            return False
        user.generated = 0
        user.right = 0
        user.wrong = 0
        user.save()
        return True
    finally:
        database.close()
