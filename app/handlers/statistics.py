from telebot import TeleBot

from app.keyboards.inline import generate_only_keyboard
from app.services.statistics_image import render_statistics_chart
from app.services.stats_repository import get_user_stats


def register_statistics_handlers(bot: TeleBot) -> None:
    @bot.message_handler(commands=["statistics"])
    def handle_statistics(message) -> None:
        try:
            # bot.send_message(message.chat.id, "statistics: start")

            stats = get_user_stats(message.from_user.id)
            # bot.send_message(message.chat.id, f"statistics: stats ok -> {stats}")

            chart_path = render_statistics_chart(
                user_id=message.from_user.id,
                username=message.from_user.username,
                generated=stats["generated"],
                right=stats["right"],
                wrong=stats["wrong"],
            )
            # bot.send_message(message.chat.id, f"statistics: image ok -> {chart_path}")

            with open(chart_path, "rb") as photo:
                bot.send_photo(
                    chat_id=message.chat.id,
                    photo=photo,
                    reply_markup=generate_only_keyboard(),
                )

        except Exception as error:
            bot.send_message(
                message.chat.id,
                f"statistics error: {type(error).__name__}: {error}",
                reply_markup=generate_only_keyboard(),
            )
            raise
