from telebot import TeleBot

from app.config import ADMIN_IDS
from app.handlers.multi_gameplay import schedule_game_start_if_ready
from app.keyboards.reply import (
    cancel_keyboard,
    create_confirm_keyboard,
    create_player_count_keyboard,
    game_mode_keyboard,
    invite_confirm_keyboard,
    invite_cancel_keyboard,
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
    is_user_in_game,
    join_game,
    mark_game_forfeit,
    remove_game_player,
)
from app.services.multi_state import (
    get_multi_state,
    get_runtime_state,
    reset_multi_state,
)
from app.services.stats_repository import (
    get_user_by_username,
    get_registered_user_by_username,
    is_user_registered,
)


TOP_MULTI_MENUS = {
    "multi_menu",
    "multi_join_list",
    "multi_ended_list",
}


def _format_username(username: str | None) -> str:
    if username:
        return f"@{username}"
    return "без username"


def _normalize_username(username: str) -> str:
    return username.strip().lstrip("@")


def _game_description() -> str:
    return (
        "Это игра с фразеологизмами: бот показывает перемешанные части фразы, "
        "а игроки пытаются угадать правильный ответ."
    )


def _build_invite_link(bot: TeleBot, game_id: int) -> str:
    bot_username = bot.get_me().username
    return f"https://t.me/{bot_username}?start=invite_{game_id}"


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


def _notify_about_invite_decline(
    bot: TeleBot,
    game_id: int,
    username: str | None,
) -> None:
    game = get_game(game_id)
    if game is None:
        return

    bot.send_message(
        game.creator_user_id,
        (
            f"Пользователь {_format_username(username)} отказался играть.\n"
            "Ожидаем подключения остальных игроков."
        ),
    )


def register_multi_message_handlers(bot: TeleBot) -> None:
    @bot.message_handler(
        func=lambda message: message.text == "Create"
        and get_menu_state(message.from_user.id) in TOP_MULTI_MENUS
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
                reply_markup=invite_cancel_keyboard(is_admin=is_admin),
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
            "multi_invite_username",
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
            "multi_invite_username",
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
            "multi_invite_username",
            "multi_join_confirm",
            "multi_waiting_joined",
            "multi_round_active",
            "multi_waiting_next_round",
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
        current_menu = get_menu_state(message.from_user.id)

        if current_menu == "multi_join_confirm":
            if state.selected_game_id:
                _notify_about_invite_decline(
                    bot=bot,
                    game_id=state.selected_game_id,
                    username=message.from_user.username,
                )

            reset_multi_state(message.from_user.id)
            set_menu_state(message.from_user.id, "multi_menu")
            bot.send_message(
                message.chat.id,
                "Действие отменено.",
                reply_markup=multi_game_keyboard(is_admin=is_admin),
            )
            return

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
        elif game.status == "started":
            runtime = get_runtime_state(game.id)
            mark_game_forfeit(
                game_id=game.id,
                user_id=canceled_user_id,
                username=canceled_username,
                total_rounds=runtime.total_rounds,
            )
            remove_game_player(game.id, canceled_user_id)
            runtime.answered_correctly.discard(canceled_user_id)
            runtime.attempts_left.pop(canceled_user_id, None)

            for participant in get_game_participants(game.id):
                bot.send_message(
                    participant["user_id"],
                    f"Игрок {_format_username(canceled_username)} покинул игру.",
                )

            reset_multi_state(message.from_user.id)
            set_menu_state(message.from_user.id, "multi_menu")
            bot.send_message(
                message.chat.id,
                "Ты покинул игру. Все ответы засчитаны как неправильные.",
                reply_markup=multi_game_keyboard(is_admin=is_admin),
            )
            return
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

    @bot.message_handler(
        func=lambda message: message.text == "Invite"
        and get_menu_state(message.from_user.id) == "multi_waiting_created"
    )
    def handle_invite(message) -> None:
        if not is_user_registered(message.from_user.id):
            set_menu_state(message.from_user.id, "registration")
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        state = get_multi_state(message.from_user.id)
        game = get_game(state.selected_game_id) if state.selected_game_id else None
        is_admin = message.from_user.id in ADMIN_IDS

        if game is None or game.status != "open":
            reset_multi_state(message.from_user.id)
            set_menu_state(message.from_user.id, "multi_menu")
            bot.send_message(
                message.chat.id,
                "Игра уже недоступна.",
                reply_markup=multi_game_keyboard(is_admin=is_admin),
            )
            return

        if game.creator_user_id != message.from_user.id:
            bot.send_message(
                message.chat.id,
                "Приглашать игроков может только создатель игры.",
                reply_markup=cancel_keyboard(is_admin=is_admin),
            )
            return

        set_menu_state(message.from_user.id, "multi_invite_username")
        bot.send_message(
            message.chat.id,
            "Введите username пользователя.",
            reply_markup=cancel_keyboard(is_admin=is_admin),
        )

    @bot.message_handler(
        func=lambda message: bool(message.text)
        and not message.text.startswith("/")
        and get_menu_state(message.from_user.id) == "multi_invite_username",
        content_types=["text"],
    )
    def handle_invite_username(message) -> None:
        if not is_user_registered(message.from_user.id):
            set_menu_state(message.from_user.id, "registration")
            bot.send_message(
                message.chat.id,
                "Сначала зарегистрируйся.",
                reply_markup=registration_keyboard(),
            )
            return

        state = get_multi_state(message.from_user.id)
        game = get_game(state.selected_game_id) if state.selected_game_id else None
        is_admin = message.from_user.id in ADMIN_IDS

        if game is None or game.status != "open":
            reset_multi_state(message.from_user.id)
            set_menu_state(message.from_user.id, "multi_menu")
            bot.send_message(
                message.chat.id,
                "Игра уже недоступна.",
                reply_markup=multi_game_keyboard(is_admin=is_admin),
            )
            return

        username = _normalize_username(message.text or "")
        invited_user = get_registered_user_by_username(username)
        known_user = invited_user or get_user_by_username(username)

        set_menu_state(message.from_user.id, "multi_waiting_created")

        if known_user is None:
            invite_link = _build_invite_link(bot, game.id)
            bot.send_message(
                message.chat.id,
                (
                    f"Пользователь @{username} ещё не открывал бота.\n"
                    "Перешли ему эту ссылку для приглашения:\n"
                    f"{invite_link}"
                ),
                reply_markup=invite_cancel_keyboard(is_admin=is_admin),
            )
            return

        if known_user.user_id == message.from_user.id:
            bot.send_message(
                message.chat.id,
                "Нельзя пригласить самого себя.",
                reply_markup=invite_cancel_keyboard(is_admin=is_admin),
            )
            return

        if is_user_in_game(game.id, known_user.user_id):
            bot.send_message(
                message.chat.id,
                f"Пользователь @{known_user.username} уже в этой игре.",
                reply_markup=invite_cancel_keyboard(is_admin=is_admin),
            )
            return

        invited_state = get_multi_state(known_user.user_id)
        invited_state.selected_game_id = game.id

        bot.send_message(
            message.chat.id,
            (
                f"Приглашение к игре №{game.id} успешно отправлено "
                f"пользователю @{known_user.username}"
            ),
            reply_markup=invite_cancel_keyboard(is_admin=is_admin),
        )

        creator_username = _format_username(message.from_user.username)
        invited_is_admin = known_user.user_id in ADMIN_IDS

        if invited_user is None:
            set_menu_state(known_user.user_id, "registration")
            bot.send_message(
                known_user.user_id,
                (
                    f"{_game_description()}\n\n"
                    f"Пользователь {creator_username} приглашает Вас поиграть.\n"
                    "Для участия нужно пройти регистрацию."
                ),
                reply_markup=registration_keyboard(),
            )
            return

        set_menu_state(known_user.user_id, "multi_join_confirm")
        bot.send_message(
            known_user.user_id,
            (
                f"Пользователь {creator_username} приглашает Вас поиграть.\n"
                "Подтверди присоединение."
            ),
            reply_markup=invite_confirm_keyboard(is_admin=invited_is_admin),
        )
