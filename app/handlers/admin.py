from telebot import TeleBot

from app.config import ADMIN_IDS
from app.keyboards.inline import generate_only_keyboard
from app.keyboards.reply import (
    admin_entry_keyboard,
    admin_main_keyboard,
    admin_user_actions_keyboard,
)
from app.services.stats_repository import (
    get_user_by_stats_id,
    list_users_stats,
    reset_user_stats_by_stats_id,
)


_admin_context: dict[int, dict] = {}


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def set_selected_user(admin_id: int, stats_id: int) -> None:
    _admin_context.setdefault(admin_id, {})
    _admin_context[admin_id]["selected_stats_id"] = stats_id


def get_selected_user_id(admin_id: int) -> int | None:
    return _admin_context.get(admin_id, {}).get("selected_stats_id")


def clear_selected_user(admin_id: int) -> None:
    if admin_id in _admin_context:
        _admin_context[admin_id].pop("selected_stats_id", None)


def format_user_stats_text(user) -> str:
    no_answer = max(0, user.generated - user.right - user.wrong)
    username = f"@{user.username}" if user.username else "—"

    return (
        f"ID в таблице userstats: <b>{user.id}</b>\n"
        f"Telegram user_id: <code>{user.user_id}</code>\n"
        f"Username: {username}\n\n"
        f"Generated: <b>{user.generated}</b>\n"
        f"Right: <b>{user.right}</b>\n"
        f"Wrong: <b>{user.wrong}</b>\n"
        f"No answer: <b>{no_answer}</b>"
    )


def register_admin_handlers(bot: TeleBot) -> None:
    @bot.message_handler(commands=["admin"])
    def handle_admin_command(message) -> None:
        if not is_admin(message.from_user.id):
            return

        clear_selected_user(message.from_user.id)
        bot.send_message(
            message.chat.id,
            "Админ-панель открыта.",
            reply_markup=admin_main_keyboard(),
        )

    @bot.message_handler(
        func=lambda message: is_admin(message.from_user.id)
        and message.text == "Админ-панель"
    )
    def handle_admin_panel(message) -> None:
        clear_selected_user(message.from_user.id)
        bot.send_message(
            message.chat.id,
            "Админ-панель открыта.",
            reply_markup=admin_main_keyboard(),
        )

    @bot.message_handler(
        func=lambda message: is_admin(message.from_user.id)
        and message.text == "Список пользователей"
    )
    def handle_users_list(message) -> None:
        users = list_users_stats(limit=100)

        if not users:
            bot.send_message(
                message.chat.id,
                "В таблице userstats пока нет пользователей.",
                reply_markup=admin_main_keyboard(),
            )
            return

        lines = [
            "<b>Список пользователей</b>",
            "Отправь цифрой ID из таблицы userstats:\n",
        ]
        for user in users:
            username = f"@{user['username']}" if user["username"] else "—"
            lines.append(
                f"{user['id']} — {username} "
                f"(tg: <code>{user['user_id']}</code>, gen: {user['generated']})"
            )

        bot.send_message(
            message.chat.id,
            "\n".join(lines),
            reply_markup=admin_main_keyboard(),
        )

    @bot.message_handler(
        func=lambda message: is_admin(message.from_user.id)
        and bool(message.text)
        and message.text.isdigit()
    )
    def handle_user_select(message) -> None:
        stats_id = int(message.text)
        user = get_user_by_stats_id(stats_id)

        if user is None:
            bot.send_message(
                message.chat.id,
                "Пользователь с таким ID в таблице userstats не найден.",
                reply_markup=admin_main_keyboard(),
            )
            return

        set_selected_user(message.from_user.id, stats_id)
        bot.send_message(
            message.chat.id,
            "Пользователь выбран.\nТеперь доступны действия:",
            reply_markup=admin_user_actions_keyboard(),
        )

    @bot.message_handler(
        func=lambda message: is_admin(message.from_user.id)
        and message.text == "current statistic"
    )
    def handle_current_statistic(message) -> None:
        stats_id = get_selected_user_id(message.from_user.id)
        if stats_id is None:
            bot.send_message(
                message.chat.id,
                "Сначала выбери пользователя по ID из таблицы userstats.",
                reply_markup=admin_main_keyboard(),
            )
            return

        user = get_user_by_stats_id(stats_id)
        if user is None:
            clear_selected_user(message.from_user.id)
            bot.send_message(
                message.chat.id,
                "Пользователь больше не найден.",
                reply_markup=admin_main_keyboard(),
            )
            return

        bot.send_message(
            message.chat.id,
            format_user_stats_text(user),
            reply_markup=admin_user_actions_keyboard(),
        )

    @bot.message_handler(
        func=lambda message: is_admin(message.from_user.id)
        and message.text == "drop statistic"
    )
    def handle_drop_statistic(message) -> None:
        stats_id = get_selected_user_id(message.from_user.id)
        if stats_id is None:
            bot.send_message(
                message.chat.id,
                "Сначала выбери пользователя по ID из таблицы userstats.",
                reply_markup=admin_main_keyboard(),
            )
            return

        success = reset_user_stats_by_stats_id(stats_id)
        if not success:
            clear_selected_user(message.from_user.id)
            bot.send_message(
                message.chat.id,
                "Не удалось сбросить статистику: пользователь не найден.",
                reply_markup=admin_main_keyboard(),
            )
            return

        user = get_user_by_stats_id(stats_id)
        bot.send_message(
            message.chat.id,
            "Статистика сброшена на нули.\n\n" + format_user_stats_text(user),
            reply_markup=admin_user_actions_keyboard(),
        )

    @bot.message_handler(
        func=lambda message: is_admin(message.from_user.id) and message.text == "Назад"
    )
    def handle_back(message) -> None:
        clear_selected_user(message.from_user.id)
        bot.send_message(
            message.chat.id,
            "Выход из админ-панели.",
            reply_markup=admin_entry_keyboard(),
        )
        bot.send_message(
            message.chat.id,
            "Игровая кнопка ниже:",
            reply_markup=generate_only_keyboard(),
        )
