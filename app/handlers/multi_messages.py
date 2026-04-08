from telebot import TeleBot

from app.config import ADMIN_IDS
from app.keyboards.reply import (
    cancel_keyboard,
    create_confirm_keyboard,
    create_player_count_keyboard,
    game_mode_keyboard,
    join_confirm_keyboard,
    multi_game_keyboard,
    registration_keyboard,
)
from app.services.multi_repository import (
    cancel_game,
    create_game,
    get_game,
    get_game_participants,
    join_game,
)
from app.services.multi_state import get_multi_state, reset_multi_state
from app.services.stats_repository import is_user_registered


def _format_username(username: str | None) -> str:
    if username:
        return f"@{username}"
    return "без username"


def _notify_game_members(
    bot: TeleBot,
    game_id: int,
    joined_username: str | None,
    max_players: int,
) -> None:
    participants = get_game_participants(game_id)
    current_count = len(participants)
    left_count = max(0, max_players - current_count)
    username_text = _format_username(joined_username)

    for participant in participants:
        bot.send_message(
            participant["user_id"],
            (f"Присоединился игрок {username_text}. " f"Ждем еще {left_count} игроков"),
        )


def register_multi_message_handlers(bot: TeleBot) -> None:
    @bot.message_handler(func=lambda message: message.text == "Create")
    def handle_create(message) -> None:
        if not is_user_registered(message.from_user.id):
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        is_admin = message.from_user.id in ADMIN_IDS
        state = get_multi_state(message.from_user.id)
        state.menu_level = "create_choose_count"
        state.selected_player_count = None
        state.selected_game_id = None

        bot.send_message(
            message.chat.id,
            "Выберите количество игроков",
            reply_markup=create_player_count_keyboard(is_admin=is_admin),
        )

    @bot.message_handler(func=lambda message: message.text in {"2", "3", "4", "5"})
    def handle_create_count(message) -> None:
        if not is_user_registered(message.from_user.id):
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        state = get_multi_state(message.from_user.id)
        if state.menu_level != "create_choose_count":
            return

        is_admin = message.from_user.id in ADMIN_IDS
        state.selected_player_count = int(message.text)
        state.menu_level = "create_confirm"

        bot.send_message(
            message.chat.id,
            f"Количество игроков: {state.selected_player_count}",
            reply_markup=create_confirm_keyboard(is_admin=is_admin),
        )

    @bot.message_handler(func=lambda message: message.text == "Start Game")
    def handle_start_game(message) -> None:
        if not is_user_registered(message.from_user.id):
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        state = get_multi_state(message.from_user.id)
        is_admin = message.from_user.id in ADMIN_IDS

        if state.menu_level == "create_confirm" and state.selected_player_count:
            game = create_game(
                creator_user_id=message.from_user.id,
                creator_username=message.from_user.username,
                max_players=state.selected_player_count,
            )
            state.selected_game_id = game.id
            state.menu_level = "created_waiting"

            bot.send_message(
                message.chat.id,
                "Игра создана. Ожидаем подключения остальных игроков.",
                reply_markup=cancel_keyboard(is_admin=is_admin),
            )
            return

        if state.menu_level == "join_confirm" and state.selected_game_id:
            ok, msg = join_game(
                game_id=state.selected_game_id,
                user_id=message.from_user.id,
                username=message.from_user.username,
            )
            if not ok:
                reset_multi_state(message.from_user.id)
                bot.send_message(
                    message.chat.id,
                    msg,
                    reply_markup=multi_game_keyboard(is_admin=is_admin),
                )
                return

            game = get_game(state.selected_game_id)
            state.menu_level = "joined_waiting"

            bot.send_message(
                message.chat.id,
                "Ты присоединился к игре. Ожидаем остальных игроков.",
                reply_markup=cancel_keyboard(is_admin=is_admin),
            )

            if game:
                _notify_game_members(
                    bot=bot,
                    game_id=game.id,
                    joined_username=message.from_user.username,
                    max_players=game.max_players,
                )
            return

    @bot.message_handler(func=lambda message: message.text == "Back")
    def handle_back(message) -> None:
        if not is_user_registered(message.from_user.id):
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        state = get_multi_state(message.from_user.id)
        is_admin = message.from_user.id in ADMIN_IDS

        if state.menu_level in {
            "create_choose_count",
            "create_confirm",
            "join_confirm",
        }:
            reset_multi_state(message.from_user.id)
            bot.send_message(
                message.chat.id,
                "Выбери действие.",
                reply_markup=multi_game_keyboard(is_admin=is_admin),
            )
            return

        reset_multi_state(message.from_user.id)
        bot.send_message(
            message.chat.id,
            "Выбери режим игры.",
            reply_markup=game_mode_keyboard(is_admin=is_admin),
        )

    @bot.message_handler(func=lambda message: message.text == "Cancel")
    def handle_cancel(message) -> None:
        if not is_user_registered(message.from_user.id):
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        state = get_multi_state(message.from_user.id)
        is_admin = message.from_user.id in ADMIN_IDS

        if state.selected_game_id:
            cancel_game(state.selected_game_id, message.from_user.id)

        reset_multi_state(message.from_user.id)
        bot.send_message(
            message.chat.id,
            "Действие отменено.",
            reply_markup=multi_game_keyboard(is_admin=is_admin),
        )
