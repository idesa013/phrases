from telebot import TeleBot

from app.keyboards.inline import generate_only_keyboard
from app.services.statistics_image import render_statistics_chart
from app.services.stats_repository import get_user_stats


def register_statistics_handlers(bot: TeleBot) -> None:
    @bot.message_handler(commands=["statistics"])
    def handle_statistics(message) -> None:
        stats = get_user_stats(message.from_user.id)

        generated = stats["generated"]
        right = stats["right"]
        wrong = stats["wrong"]
        no_answer = max(0, generated - right - wrong)

        chart_path = render_statistics_chart(
            user_id=message.from_user.id,
            generated=generated,
            right=right,
            wrong=wrong,
        )

        caption = (
            f"📊 <b>Твоя статистика</b>\n\n"
            f"Всего сгенерировано: <b>{generated}</b>\n"
            f"✅ Правильных: <b>{right}</b>\n"
            f"❌ Неправильных: <b>{wrong}</b>\n"
            f"⚪ Без ответа: <b>{no_answer}</b>"
        )

        with open(chart_path, "rb") as photo:
            bot.send_photo(
                chat_id=message.chat.id,
                photo=photo,
                caption=caption,
                reply_markup=generate_only_keyboard(),
            )
