from telebot import TeleBot

from app.config import ADMIN_IDS
from app.handlers.multi_gameplay import schedule_game_start_if_ready
from app.keyboards.reply import (
    cancel_keyboard,
    create_confirm_keyboard,
    create_player_count_keyboard,
    game_mode_keyboard,
    multi_game_keyboard,
    registration_keyboard,
)
from app.services.menu_state import get_menu_state, set_menu_state
from app.services.multi_repository import (
    cancel_game,
    clear_game_players,
    create_game,
    get_game,
    get_game_participants,
    get_start_delay_seconds,
    join_game,
)
from app.services.multi_state import get_multi_state, reset_multi_state
from app.services.stats_repository import is_user_registered


def _format_username(username: str | None) -> str:
    if username:
        return f"@{username}"
    return "без username"


def _notify_about_join(
    bot: TeleBot,
    game_id: int,
    joined_user_id: int,
    joined_username: str | None,
    max_players: int,
) -> None:
    participants = get_game_participants(game_id)
    current_count = len(participants)
    left_count = max(0, max_players - current_count)
    username_text = _format_username(joined_username)

    for participant in participants:
        if participant["user_id"] == joined_user_id:
            continue

        if left_count == 0:
            delay_seconds = get_start_delay_seconds()
            bot.send_message(
                participant["user_id"],
                (
                    f"Присоединился последний игрок {username_text}. "
                    f"Игра начнется через {delay_seconds} секунд"
                ),
            )
        else:
            bot.send_message(
                participant["user_id"],
                (
                    f"Присоединился игрок {username_text}. "
                    f"Ждем еще {left_count} игроков"
                ),
            )


def _notify_about_player_cancel(
    bot: TeleBot,
    game_id: int,
    canceled_user_id: int,
    canceled_username: str | None,
    max_players: int,
) -> None:
    participants = get_game_participants(game_id)
    current_count = len(participants)
    left_count = max(0, max_players - current_count)
    username_text = _format_username(canceled_username)

    for participant in participants:
        if participant["user_id"] == canceled_user_id:
            continue

        bot.send_message(
            participant["user_id"],
            (
                f"Игрок {username_text} отказался от участия. "
                f"Ждем еще {left_count} игроков"
            ),
        )


def _notify_about_creator_cancel(
    bot: TeleBot,
    participants_before_cancel: list[dict],
    creator_user_id: int,
    creator_username: str | None,
) -> None:
    username_text = _format_username(creator_username)

    for participant in participants_before_cancel:
        if participant["user_id"] == creator_user_id:
            continue

        participant_id = participant["user_id"]
        is_admin = participant_id in ADMIN_IDS

        reset_multi_state(participant_id)
        set_menu_state(participant_id, "multi_menu")

        bot.send_message(
            participant_id,
            f"Игрок {username_text} отменил игру",
            reply_markup=multi_game_keyboard(is_admin=is_admin),
        )


def register_multi_message_handlers(bot: TeleBot) -> None:
    @bot.message_handler(
        func=lambda message: message.text == "Create"
        and get_menu_state(message.from_user.id) == "multi_menu"
    )
    def handle_create(message) -> None:
        if not is_user_registered(message.from_user.id):
            set_menu_state(message.from_user.id, "registration")
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        is_admin = message.from_user.id in ADMIN_IDS
        state = get_multi_state(message.from_user.id)
        state.selected_player_count = None
        state.selected_game_id = None

        set_menu_state(message.from_user.id, "multi_create_choose_count")
        bot.send_message(
            message.chat.id,
            "Выберите количество игроков",
            reply_markup=create_player_count_keyboard(is_admin=is_admin),
        )

    @bot.message_handler(
        func=lambda message: message.text in {"2", "3", "4", "5"}
        and get_menu_state(message.from_user.id) == "multi_create_choose_count"
    )
    def handle_create_count(message) -> None:
        if not is_user_registered(message.from_user.id):
            set_menu_state(message.from_user.id, "registration")
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        state = get_multi_state(message.from_user.id)
        is_admin = message.from_user.id in ADMIN_IDS

        state.selected_player_count = int(message.text)

        set_menu_state(message.from_user.id, "multi_create_confirm")
        bot.send_message(
            message.chat.id,
            f"Количество игроков: {state.selected_player_count}",
            reply_markup=create_confirm_keyboard(is_admin=is_admin),
        )

    @bot.message_handler(
        func=lambda message: message.text == "Start Game"
        and get_menu_state(message.from_user.id)
        in {
            "multi_create_confirm",
            "multi_join_confirm",
        }
    )
    def handle_start_game(message) -> None:
        if not is_user_registered(message.from_user.id):
            set_menu_state(message.from_user.id, "registration")
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        state = get_multi_state(message.from_user.id)
        is_admin = message.from_user.id in ADMIN_IDS
        current_menu = get_menu_state(message.from_user.id)

        if current_menu == "multi_create_confirm" and state.selected_player_count:
            game = create_game(
                creator_user_id=message.from_user.id,
                creator_username=message.from_user.username,
                max_players=state.selected_player_count,
            )
            state.selected_game_id = game.id

            set_menu_state(message.from_user.id, "multi_waiting_created")
            bot.send_message(
                message.chat.id,
                "Игра создана. Ожидаем подключения остальных игроков.",
                reply_markup=cancel_keyboard(is_admin=is_admin),
            )
            return

        if current_menu == "multi_join_confirm" and state.selected_game_id:
            ok, msg = join_game(
                game_id=state.selected_game_id,
                user_id=message.from_user.id,
                username=message.from_user.username,
            )
            if not ok:
                reset_multi_state(message.from_user.id)
                set_menu_state(message.from_user.id, "multi_menu")
                bot.send_message(
                    message.chat.id,
                    msg,
                    reply_markup=multi_game_keyboard(is_admin=is_admin),
                )
                return

            game = get_game(state.selected_game_id)
            set_menu_state(message.from_user.id, "multi_waiting_joined")

            if game and game.status == "ready":
                delay = get_start_delay_seconds()
                bot.send_message(
                    message.chat.id,
                    f"Ты присоединился к игре. Игра начнется через {delay} секунд.",
                    reply_markup=cancel_keyboard(is_admin=is_admin),
                )
            else:
                bot.send_message(
                    message.chat.id,
                    "Ты присоединился к игре. Ожидаем остальных игроков.",
                    reply_markup=cancel_keyboard(is_admin=is_admin),
                )

            if game:
                _notify_about_join(
                    bot=bot,
                    game_id=game.id,
                    joined_user_id=message.from_user.id,
                    joined_username=message.from_user.username,
                    max_players=game.max_players,
                )

                if game.status == "ready":
                    schedule_game_start_if_ready(bot, game.id)

    @bot.message_handler(
        func=lambda message: message.text == "Back"
        and get_menu_state(message.from_user.id)
        in {
            "multi_menu",
            "multi_create_choose_count",
            "multi_create_confirm",
            "multi_join_confirm",
            "multi_join_list",
            "multi_ended_list",
        }
    )
    def handle_multi_back(message) -> None:
        if not is_user_registered(message.from_user.id):
            set_menu_state(message.from_user.id, "registration")
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        is_admin = message.from_user.id in ADMIN_IDS
        current_menu = get_menu_state(message.from_user.id)

        if current_menu in {
            "multi_create_choose_count",
            "multi_create_confirm",
            "multi_join_confirm",
            "multi_join_list",
            "multi_ended_list",
        }:
            reset_multi_state(message.from_user.id)
            set_menu_state(message.from_user.id, "multi_menu")
            bot.send_message(
                message.chat.id,
                "Выбери действие.",
                reply_markup=multi_game_keyboard(is_admin=is_admin),
            )
            return

        if current_menu == "multi_menu":
            reset_multi_state(message.from_user.id)
            set_menu_state(message.from_user.id, "root")
            bot.send_message(
                message.chat.id,
                "Выбери режим игры.",
                reply_markup=game_mode_keyboard(is_admin=is_admin),
            )

    @bot.message_handler(
        func=lambda message: message.text == "Cancel"
        and get_menu_state(message.from_user.id)
        in {
            "multi_waiting_created",
            "multi_waiting_joined",
        }
    )
    def handle_cancel(message) -> None:
        if not is_user_registered(message.from_user.id):
            set_menu_state(message.from_user.id, "registration")
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        state = get_multi_state(message.from_user.id)
        is_admin = message.from_user.id in ADMIN_IDS

        if not state.selected_game_id:
            reset_multi_state(message.from_user.id)
            set_menu_state(message.from_user.id, "multi_menu")
            bot.send_message(
                message.chat.id,
                "Действие отменено.",
                reply_markup=multi_game_keyboard(is_admin=is_admin),
            )
            return

        game = get_game(state.selected_game_id)
        if game is None:
            reset_multi_state(message.from_user.id)
            set_menu_state(message.from_user.id, "multi_menu")
            bot.send_message(
                message.chat.id,
                "Игра уже недоступна.",
                reply_markup=multi_game_keyboard(is_admin=is_admin),
            )
            return

        canceled_user_id = message.from_user.id
        canceled_username = message.from_user.username

        if game.creator_user_id == canceled_user_id:
            participants_before_cancel = get_game_participants(game.id)

            cancel_game(game.id, canceled_user_id)

            _notify_about_creator_cancel(
                bot=bot,
                participants_before_cancel=participants_before_cancel,
                creator_user_id=canceled_user_id,
                creator_username=canceled_username,
            )

            clear_game_players(game.id)
        else:
            cancel_game(game.id, canceled_user_id)

            _notify_about_player_cancel(
                bot=bot,
                game_id=game.id,
                canceled_user_id=canceled_user_id,
                canceled_username=canceled_username,
                max_players=game.max_players,
            )

        reset_multi_state(message.from_user.id)
        set_menu_state(message.from_user.id, "multi_menu")
        bot.send_message(
            message.chat.id,
            "Действие отменено.",
            reply_markup=multi_game_keyboard(is_admin=is_admin),
        )
