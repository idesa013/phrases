from telebot import TeleBot

from app.config import ADMIN_IDS
from app.keyboards.game_reply import join_confirm_keyboard
from app.keyboards.multi_inline import open_games_keyboard
from app.services.multi_repository import count_open_games, get_game, list_open_games
from app.services.multi_state import get_multi_state


def _send_games_page(bot: TeleBot, chat_id: int, page: int) -> None:
    per_page = 15
    offset = (page - 1) * per_page
    games = list_open_games(limit=per_page, offset=offset)
    total_games = count_open_games()

    if not games:
        bot.send_message(chat_id, "Открытых игр нет.")
        return

    bot.send_message(
        chat_id,
        "Список открытых игр:",
        reply_markup=open_games_keyboard(games, page, total_games),
    )


def register_multi_callback_handlers(bot: TeleBot) -> None:
    @bot.message_handler(func=lambda message: message.text == "Join")
    def handle_join(message) -> None:
        state = get_multi_state(message.from_user.id)
        state.menu_level = "join_list"
        state.games_page = 1
        _send_games_page(bot, message.chat.id, 1)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("games_page:"))
    def handle_games_page(call) -> None:
        page_raw = call.data.split(":", 1)[1]
        if page_raw == "stay":
            bot.answer_callback_query(call.id)
            return

        page = int(page_raw)
        state = get_multi_state(call.from_user.id)
        state.games_page = page

        games = list_open_games(limit=15, offset=(page - 1) * 15)
        total_games = count_open_games()

        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=open_games_keyboard(games, page, total_games),
        )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("join_game_select:")
    )
    def handle_join_game_select(call) -> None:
        game_id = int(call.data.split(":", 1)[1])
        game = get_game(game_id)
        bot.answer_callback_query(call.id)

        if game is None or game.status != "open":
            bot.send_message(call.message.chat.id, "Эта игра уже недоступна.")
            return

        state = get_multi_state(call.from_user.id)
        state.selected_game_id = game_id
        state.menu_level = "join_confirm"

        is_admin = call.from_user.id in ADMIN_IDS
        bot.send_message(
            call.message.chat.id,
            f"Выбрана игра #{game_id}. Подтверди присоединение.",
            reply_markup=join_confirm_keyboard(is_admin=is_admin),
        )
