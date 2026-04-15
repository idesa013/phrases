import threading

from telebot import TeleBot

from app.config import ADMIN_IDS
from app.keyboards.reply import (
    cancel_keyboard,
    multi_game_keyboard,
    registration_keyboard,
)
from app.services.menu_state import get_menu_state, set_menu_state
from app.services.multi_repository import (
    get_answer_attempts,
    get_answer_time_seconds,
    get_game,
    get_game_leaderboard,
    get_game_participants,
    get_next_round_delay_seconds,
    get_rounds_count,
    get_start_delay_seconds,
    increment_game_right,
    increment_game_wrong,
    init_round_stats,
    is_user_in_game,
    set_game_status,
)
from app.services.multi_state import (
    get_multi_state,
    get_runtime_state,
    remove_runtime_state,
    reset_multi_state,
)
from app.services.phrase_repository import get_random_phrase
from app.services.image_generator import PhraseShuffleError, render_phrase_image
from app.services.stats_repository import is_user_registered
from app.utils.text import normalize_answer
from app.services.multi_statistics_image import render_multi_statistics_image
from app.services.multi_results_view import send_game_results


def _format_username(username: str | None) -> str:
    if username:
        return f"@{username}"
    return "без username"


# 🔥 ВОТ ЭТА ФУНКЦИЯ ИЗМЕНЕНА
def _build_leaderboard_text(game_id: int, total_rounds: int) -> str:
    leaderboard = get_game_leaderboard(game_id)

    lines = [
        f"Игра № {game_id} окончена.",
        f"Всего заданий: {total_rounds}",
        "",
        "Статистика ответов игроков:",
    ]

    if not leaderboard:
        lines.append("Статистика пока отсутствует.")
        return "\n".join(lines)

    for index, item in enumerate(leaderboard, start=1):
        username = _format_username(item["username"])
        lines.append(
            f"{index}. {username} — "
            f"Правильных: {item['right']}, "
            f"Неправильных: {item['wrong']}"
        )

    return "\n".join(lines)


def _finish_game(bot: TeleBot, game_id: int) -> None:
    game = get_game(game_id)
    runtime = get_runtime_state(game_id)

    if game is None:
        remove_runtime_state(game_id)
        return

    participants = get_game_participants(game_id)
    set_game_status(game_id, "ended")

    # 👇 теперь передаём количество раундов
    # leaderboard = get_game_leaderboard(game_id)
    # text = _build_leaderboard_text(game_id, runtime.total_rounds)
    # stat_image_path = render_multi_statistics_image(
    #     game_id=game_id,
    #     total_rounds=runtime.total_rounds,
    #     leaderboard=leaderboard,
    # )

    for participant in participants:
        user_id = participant["user_id"]
        is_admin = user_id in ADMIN_IDS

        reset_multi_state(user_id)
        set_menu_state(user_id, "multi_menu")

        send_game_results(
            bot=bot,
            chat_id=user_id,
            game_id=game_id,
            is_admin=is_admin,
        )

    remove_runtime_state(game_id)


# --- дальше код БЕЗ изменений ---


def _finalize_round(bot: TeleBot, game_id: int) -> None:
    game = get_game(game_id)
    runtime = get_runtime_state(game_id)

    if game is None or game.status in {"canceled", "ended"}:
        remove_runtime_state(game_id)
        return

    if not runtime.round_active:
        return

    runtime.round_active = False
    participants = get_game_participants(game_id)
    phrase = runtime.phrase or ""

    for participant in participants:
        user_id = participant["user_id"]
        username = participant["username"]

        if user_id not in runtime.answered_correctly:
            increment_game_wrong(game_id, user_id, username)
            bot.send_message(
                user_id,
                (
                    f"Время вышло.\n"
                    f"Правильный ответ: {phrase}\n"
                    f"Ответ неправильный или не введен."
                ),
            )
        else:
            bot.send_message(
                user_id,
                (
                    f"Время вышло.\n"
                    f"Правильный ответ: {phrase}\n"
                    f"Ты ответил правильно."
                ),
            )

    if runtime.current_round >= runtime.total_rounds:
        _finish_game(bot, game_id)
        return

    delay = get_next_round_delay_seconds()
    for participant in participants:
        bot.send_message(
            participant["user_id"],
            f"Следующее задание через {delay} секунд",
        )
        set_menu_state(participant["user_id"], "multi_waiting_next_round")

    if runtime.next_round_scheduled:
        return

    runtime.next_round_scheduled = True
    timer = threading.Timer(delay, _start_next_round, args=(bot, game_id))
    timer.daemon = True
    timer.start()


def _start_next_round(bot: TeleBot, game_id: int) -> None:
    game = get_game(game_id)
    runtime = get_runtime_state(game_id)

    runtime.next_round_scheduled = False

    if game is None or game.status in {"canceled", "ended"}:
        remove_runtime_state(game_id)
        return

    participants = get_game_participants(game_id)
    if not participants:
        set_game_status(game_id, "canceled")
        remove_runtime_state(game_id)
        return

    runtime.current_round += 1
    runtime.total_rounds = get_rounds_count()
    runtime.round_active = True
    runtime.answered_correctly = set()

    attempts_limit = get_answer_attempts()
    runtime.attempts_left = {p["user_id"]: attempts_limit for p in participants}

    try:
        phrase = get_random_phrase(exclude=runtime.used_phrases)
        image_path = render_phrase_image(phrase, game_id)
    except (ValueError, PhraseShuffleError):
        for participant in participants:
            bot.send_message(
                participant["user_id"],
                "Не нашлось фразы, которую можно хорошо перемешать.",
            )
        _finish_game(bot, game_id)
        return

    runtime.phrase = phrase
    runtime.last_phrase = phrase
    runtime.used_phrases.add(phrase)

    init_round_stats(game_id, participants)

    answer_time = get_answer_time_seconds()

    for participant in participants:
        set_menu_state(participant["user_id"], "multi_round_active")
        with open(image_path, "rb") as photo:
            bot.send_photo(
                chat_id=participant["user_id"],
                photo=photo,
                caption=(
                    f"Раунд {runtime.current_round}/{runtime.total_rounds}\n"
                    f"Время на ответ: {answer_time} сек.\n"
                    f"Количество попыток: {attempts_limit}"
                ),
                reply_markup=cancel_keyboard(
                    is_admin=participant["user_id"] in ADMIN_IDS
                ),
            )

    timer = threading.Timer(answer_time, _finalize_round, args=(bot, game_id))
    timer.daemon = True
    timer.start()


def schedule_game_start_if_ready(bot: TeleBot, game_id: int) -> None:
    game = get_game(game_id)
    if game is None or game.status != "ready":
        return

    runtime = get_runtime_state(game_id)
    if runtime.start_scheduled:
        return

    runtime.start_scheduled = True
    runtime.total_rounds = get_rounds_count()

    delay = get_start_delay_seconds()
    timer = threading.Timer(delay, _begin_game, args=(bot, game_id))
    timer.daemon = True
    timer.start()


def _begin_game(bot: TeleBot, game_id: int) -> None:
    game = get_game(game_id)
    runtime = get_runtime_state(game_id)

    runtime.start_scheduled = False

    if game is None or game.status != "ready":
        return

    set_game_status(game_id, "started")
    _start_next_round(bot, game_id)


def register_multi_gameplay_handlers(bot: TeleBot) -> None:
    @bot.message_handler(
        func=lambda message: bool(message.text)
        and not message.text.startswith("/")
        and get_menu_state(message.from_user.id) == "multi_round_active",
        content_types=["text"],
    )
    def handle_multi_answer(message) -> None:
        if not is_user_registered(message.from_user.id):
            return

        user_state = get_multi_state(message.from_user.id)
        game_id = user_state.selected_game_id

        if not game_id:
            return

        game = get_game(game_id)
        if game is None or game.status not in {"started", "ready"}:
            return

        if not is_user_in_game(game_id, message.from_user.id):
            return

        runtime = get_runtime_state(game_id)

        if not runtime.round_active or not runtime.phrase:
            return

        user_id = message.from_user.id

        if message.text == "Invite":
            bot.send_message(message.chat.id, "Приглашать можно только до начала игры.")
            return

        if user_id in runtime.answered_correctly:
            bot.send_message(message.chat.id, "Ты уже ответил правильно.")
            return

        attempts_left = runtime.attempts_left.get(user_id, 0)
        if attempts_left <= 0:
            bot.send_message(message.chat.id, "Количество попыток исчерпано.")
            return

        user_answer = normalize_answer(message.text or "")
        correct_answer = normalize_answer(runtime.phrase)

        if user_answer == correct_answer:
            runtime.answered_correctly.add(user_id)
            increment_game_right(game_id, user_id, message.from_user.username)
            bot.send_message(message.chat.id, "✅ Правильный ответ.")
            return

        attempts_left -= 1
        runtime.attempts_left[user_id] = attempts_left

        if attempts_left <= 0:
            bot.send_message(
                message.chat.id,
                "❌ Неправильно. Количество попыток исчерпано.",
            )
            return

        bot.send_message(
            message.chat.id,
            f"❌ Неправильно. Осталось попыток: {attempts_left}",
        )
