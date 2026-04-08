from telebot import TeleBot

from app.config import ADMIN_IDS
from app.keyboards.reply import game_mode_keyboard
from app.services.statistics_image import render_statistics_chart
from app.services.stats_repository import get_user_stats


def register_statistics_handlers(bot: TeleBot) -> None:
    @bot.message_handler(commands=["statistics"])
    def handle_statistics(message) -> None:
        try:
            stats = get_user_stats(message.from_user.id)
            chart_path = render_statistics_chart(
                user_id=message.from_user.id,
                username=message.from_user.username,
                generated=stats["generated"],
                right=stats["right"],
                wrong=stats["wrong"],
            )

            with open(chart_path, "rb") as photo:
                bot.send_photo(
                    chat_id=message.chat.id,
                    photo=photo,
                    reply_markup=game_mode_keyboard(
                        is_admin=message.from_user.id in ADMIN_IDS
                    ),
                )
        except Exception as error:
            bot.send_message(
                message.chat.id,
                f"statistics error: {type(error).__name__}: {error}",
                reply_markup=game_mode_keyboard(
                    is_admin=message.from_user.id in ADMIN_IDS
                ),
            )
            raise
