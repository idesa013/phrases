from telebot import TeleBot

from app.config import ADMIN_IDS
from app.keyboards.reply import (
    admin_main_keyboard,
    admin_user_actions_keyboard,
    game_mode_keyboard,
)
from app.services.admin_repository import (
    get_multi_user_stats,
    get_user_by_table_id,
    get_user_stats_by_user_id,
    list_users,
    reset_user_stats_by_user_id,
)
from app.services.menu_state import get_menu_state, set_menu_state


_admin_context: dict[int, dict] = {}


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def set_selected_user(admin_id: int, user_table_id: int) -> None:
    _admin_context.setdefault(admin_id, {})
    _admin_context[admin_id]["selected_user_table_id"] = user_table_id


def get_selected_user_id(admin_id: int) -> int | None:
    return _admin_context.get(admin_id, {}).get("selected_user_table_id")


def clear_selected_user(admin_id: int) -> None:
    if admin_id in _admin_context:
        _admin_context[admin_id].pop("selected_user_table_id", None)


def format_user_stats_text(user, stats) -> str:
    generated = stats.generated if stats is not None else 0
    right = stats.right if stats is not None else 0
    wrong = stats.wrong if stats is not None else 0
    no_answer = max(0, generated - right - wrong)

    username_value = user.username
    username = f"@{username_value}" if username_value else "—"

    return (
        f"ID в таблице user: {user.id}\n"
        f"Telegram user_id: `{user.user_id}`\n"
        f"Username: {username}\n\n"
        f"Generated: {generated}\n"
        f"Right: {right}\n"
        f"Wrong: {wrong}\n"
        f"No answer: {no_answer}"
    )


def format_multi_stats_text(user, stats: dict[str, int]) -> str:
    username = f"@{user.username}" if user.username else "—"

    return (
        f"Telegram user_id: `{user.user_id}`\n"
        f"Username: {username}\n\n"
        f"<b>Total games:</b> <b>{stats['total_games']}</b>\n"
        f"🥇 Win: {stats['win']}\n"
        f"🥈 Second place: {stats['second_place']}\n"
        f"🥉 Third place: {stats['third_place']}\n"
        f"🏅 Fourth place: {stats['fourth_place']}\n"
        f"❌ Lose: {stats['lose']}"
    )


def register_admin_handlers(bot: TeleBot) -> None:
    @bot.message_handler(commands=["admin"])
    def handle_admin_command(message) -> None:
        if not is_admin(message.from_user.id):
            return

        clear_selected_user(message.from_user.id)
        set_menu_state(message.from_user.id, "admin_menu")
        bot.send_message(
            message.chat.id,
            "Admin-panel открыт.",
            reply_markup=admin_main_keyboard(),
        )

    @bot.message_handler(
        func=lambda message: is_admin(message.from_user.id)
        and message.text == "Admin-panel"
    )
    def handle_admin_panel(message) -> None:
        clear_selected_user(message.from_user.id)
        set_menu_state(message.from_user.id, "admin_menu")
        bot.send_message(
            message.chat.id,
            "Admin-panel открыт.",
            reply_markup=admin_main_keyboard(),
        )

    @bot.message_handler(
        func=lambda message: is_admin(message.from_user.id)
        and get_menu_state(message.from_user.id) in {"admin_menu", "admin_list"}
        and message.text == "User List"
    )
    def handle_users_list(message) -> None:
        users = list_users(limit=100)
        set_menu_state(message.from_user.id, "admin_list")

        if not users:
            bot.send_message(
                message.chat.id,
                "В таблице user пока нет пользователей.",
                reply_markup=admin_main_keyboard(),
            )
            return

        lines = [
            "Список пользователей",
            "Отправь цифрой ID из таблицы user:\n",
        ]

        for user in users:
            username = f"@{user['username']}" if user["username"] else "—"
            lines.append(f"{user['id']} — {username} " f"(tg: `{user['user_id']}`)")

        bot.send_message(
            message.chat.id,
            "\n".join(lines),
            reply_markup=admin_main_keyboard(),
        )

    @bot.message_handler(
        func=lambda message: is_admin(message.from_user.id)
        and get_menu_state(message.from_user.id) == "admin_list"
        and bool(message.text)
        and message.text.isdigit()
    )
    def handle_user_select(message) -> None:
        user_table_id = int(message.text)
        user = get_user_by_table_id(user_table_id)

        if user is None:
            bot.send_message(
                message.chat.id,
                "Пользователь с таким ID в таблице user не найден.",
                reply_markup=admin_main_keyboard(),
            )
            return

        set_selected_user(message.from_user.id, user_table_id)
        set_menu_state(message.from_user.id, "admin_user_actions")
        bot.send_message(
            message.chat.id,
            "Пользователь выбран.\nТеперь доступны действия:",
            reply_markup=admin_user_actions_keyboard(),
        )

    @bot.message_handler(
        func=lambda message: is_admin(message.from_user.id)
        and get_menu_state(message.from_user.id) == "admin_user_actions"
        and message.text == "current statistic"
    )
    def handle_current_statistic(message) -> None:
        user_table_id = get_selected_user_id(message.from_user.id)

        if user_table_id is None:
            set_menu_state(message.from_user.id, "admin_menu")
            bot.send_message(
                message.chat.id,
                "Сначала выбери пользователя по ID из таблицы user.",
                reply_markup=admin_main_keyboard(),
            )
            return

        user = get_user_by_table_id(user_table_id)
        if user is None:
            clear_selected_user(message.from_user.id)
            set_menu_state(message.from_user.id, "admin_menu")
            bot.send_message(
                message.chat.id,
                "Пользователь больше не найден.",
                reply_markup=admin_main_keyboard(),
            )
            return

        stats = get_user_stats_by_user_id(user.user_id)

        bot.send_message(
            message.chat.id,
            format_user_stats_text(user, stats),
            reply_markup=admin_user_actions_keyboard(),
        )

    @bot.message_handler(
        func=lambda message: is_admin(message.from_user.id)
        and get_menu_state(message.from_user.id) == "admin_user_actions"
        and message.text == "drop statistic"
    )
    def handle_drop_statistic(message) -> None:
        user_table_id = get_selected_user_id(message.from_user.id)

        if user_table_id is None:
            set_menu_state(message.from_user.id, "admin_menu")
            bot.send_message(
                message.chat.id,
                "Сначала выбери пользователя по ID из таблицы user.",
                reply_markup=admin_main_keyboard(),
            )
            return

        user = get_user_by_table_id(user_table_id)
        if user is None:
            clear_selected_user(message.from_user.id)
            set_menu_state(message.from_user.id, "admin_menu")
            bot.send_message(
                message.chat.id,
                "Пользователь больше не найден.",
                reply_markup=admin_main_keyboard(),
            )
            return

        success = reset_user_stats_by_user_id(user.user_id)
        stats = get_user_stats_by_user_id(user.user_id)

        if not success:
            bot.send_message(
                message.chat.id,
                "Запись в таблице userstats не найдена. Сбрасывать нечего.\n\n"
                + format_user_stats_text(user, stats),
                reply_markup=admin_user_actions_keyboard(),
            )
            return

        bot.send_message(
            message.chat.id,
            "Статистика сброшена на нули.\n\n" + format_user_stats_text(user, stats),
            reply_markup=admin_user_actions_keyboard(),
        )

    @bot.message_handler(
        func=lambda message: is_admin(message.from_user.id)
        and get_menu_state(message.from_user.id) == "admin_user_actions"
        and message.text == "multi statistic"
    )
    def handle_multi_statistic(message) -> None:
        user_table_id = get_selected_user_id(message.from_user.id)

        if user_table_id is None:
            set_menu_state(message.from_user.id, "admin_menu")
            bot.send_message(
                message.chat.id,
                "Сначала выбери пользователя по ID из таблицы user.",
                reply_markup=admin_main_keyboard(),
            )
            return

        user = get_user_by_table_id(user_table_id)
        if user is None:
            clear_selected_user(message.from_user.id)
            set_menu_state(message.from_user.id, "admin_menu")
            bot.send_message(
                message.chat.id,
                "Пользователь больше не найден.",
                reply_markup=admin_main_keyboard(),
            )
            return

        stats = get_multi_user_stats(user.user_id)

        bot.send_message(
            message.chat.id,
            format_multi_stats_text(user, stats),
            reply_markup=admin_user_actions_keyboard(),
        )

    @bot.message_handler(
        func=lambda message: message.text == "Back"
        and is_admin(message.from_user.id)
        and get_menu_state(message.from_user.id)
        in {
            "admin_menu",
            "admin_list",
            "admin_user_actions",
        }
    )
    def handle_admin_back(message) -> None:
        clear_selected_user(message.from_user.id)
        set_menu_state(message.from_user.id, "root")
        bot.send_message(
            message.chat.id,
            "Выбери режим игры.",
            reply_markup=game_mode_keyboard(is_admin=True),
        )
