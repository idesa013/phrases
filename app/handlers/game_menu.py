from telebot import TeleBot

from app.config import ADMIN_IDS
from app.keyboards.inline import generate_only_keyboard
from app.keyboards.reply import (
    game_mode_keyboard,
    invite_confirm_keyboard,
    multi_game_keyboard,
    registration_keyboard,
)
from app.services.menu_state import reset_menu_state, set_menu_state
from app.services.multi_repository import get_game
from app.services.multi_state import get_multi_state, reset_multi_state
from app.services.stats_repository import is_user_registered, remember_user


def _game_description() -> str:
    return (
        "Это игра с фразеологизмами: бот показывает перемешанные части фразы, "
        "а игроки пытаются угадать правильный ответ."
    )


def _format_username(username: str | None) -> str:
    if username:
        return f"@{username}"
    return "без username"


def _parse_invite_game_id(message_text: str | None) -> int | None:
    if not message_text:
        return None

    parts = message_text.split(maxsplit=1)
    if len(parts) != 2:
        return None

    payload = parts[1]
    if not payload.startswith("invite_"):
        return None

    raw_game_id = payload.removeprefix("invite_")
    if not raw_game_id.isdigit():
        return None

    return int(raw_game_id)


def _send_invite_confirmation(
    bot: TeleBot,
    chat_id: int,
    user_id: int,
    prefix: str = "",
) -> bool:
    state = get_multi_state(user_id)
    if not state.selected_game_id:
        return False

    game = get_game(state.selected_game_id)
    if game is None or game.status != "open":
        state.selected_game_id = None
        return False

    is_admin = user_id in ADMIN_IDS
    set_menu_state(user_id, "multi_join_confirm")
    bot.send_message(
        chat_id,
        (
            f"{prefix}"
            f"Пользователь {_format_username(game.creator_username)} "
            "приглашает Вас поиграть.\n"
            "Подтверди присоединение."
        ),
        reply_markup=invite_confirm_keyboard(is_admin=is_admin),
    )
    return True


def _send_pending_invite_after_registration(bot: TeleBot, message) -> bool:
    return _send_invite_confirmation(
        bot=bot,
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        prefix="Регистрация завершена.\n",
    )


def register_game_menu_handlers(bot: TeleBot) -> None:
    @bot.message_handler(commands=["start", "help"])
    def handle_start(message) -> None:
        state = get_multi_state(message.from_user.id)
        invite_game_id = _parse_invite_game_id(message.text)
        pending_game_id = invite_game_id or state.selected_game_id

        if pending_game_id is None:
            reset_multi_state(message.from_user.id)
        reset_menu_state(message.from_user.id)
        if pending_game_id is not None:
            get_multi_state(message.from_user.id).selected_game_id = pending_game_id

        if not is_user_registered(message.from_user.id):
            remember_user(
                user_id=message.from_user.id,
                username=message.from_user.username,
                name=message.from_user.first_name,
                surname=message.from_user.last_name,
            )

            set_menu_state(message.from_user.id, "registration")
            bot.send_message(
                message.chat.id,
                f"{_game_description()}\n\nДля начала нужно пройти регистрацию.",
                reply_markup=registration_keyboard(),
            )
            return

        if pending_game_id is not None and _send_invite_confirmation(
            bot=bot,
            chat_id=message.chat.id,
            user_id=message.from_user.id,
        ):
            return

        is_admin = message.from_user.id in ADMIN_IDS
        set_menu_state(message.from_user.id, "root")
        bot.send_message(
            message.chat.id,
            "Выбери режим игры.",
            reply_markup=game_mode_keyboard(is_admin=is_admin),
        )

    @bot.message_handler(func=lambda message: message.text == "Register")
    def handle_register(message) -> None:
        from app.services.stats_repository import register_user

        register_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            name=message.from_user.first_name,
            surname=message.from_user.last_name,
        )

        if _send_pending_invite_after_registration(bot, message):
            return

        is_admin = message.from_user.id in ADMIN_IDS
        set_menu_state(message.from_user.id, "root")
        bot.send_message(
            message.chat.id,
            "Регистрация завершена.",
            reply_markup=game_mode_keyboard(is_admin=is_admin),
        )

    @bot.message_handler(func=lambda message: message.text == "Single game")
    def handle_single_game(message) -> None:
        if not is_user_registered(message.from_user.id):
            set_menu_state(message.from_user.id, "registration")
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        set_menu_state(message.from_user.id, "single_game")
        bot.send_message(
            message.chat.id,
            "Нажми кнопку ниже, чтобы сгенерировать фразу.",
            reply_markup=generate_only_keyboard(),
        )

    @bot.message_handler(func=lambda message: message.text == "Multi game")
    def handle_multi_game(message) -> None:
        if not is_user_registered(message.from_user.id):
            set_menu_state(message.from_user.id, "registration")
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        is_admin = message.from_user.id in ADMIN_IDS
        reset_multi_state(message.from_user.id)
        set_menu_state(message.from_user.id, "multi_menu")
        bot.send_message(
            message.chat.id,
            "Выбери действие.",
            reply_markup=multi_game_keyboard(is_admin=is_admin),
        )
