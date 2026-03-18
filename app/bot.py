import logging

from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.config import BOT_TOKEN, UPDATE_INTERVAL_SECONDS
from app.handlers.game import check_answer, generate_phrase
from app.handlers.start import start
from app.services.phrase_updater import update_phrases


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def run_startup_update(application: Application) -> None:
    result = update_phrases(force=True)
    logger.info("Проверка фраз при запуске: %s", result)


async def scheduled_update(context: ContextTypes.DEFAULT_TYPE) -> None:
    result = update_phrases(force=False)
    logger.info("Ежедневная проверка фраз: %s", result)


async def post_init(application: Application) -> None:
    await run_startup_update(application)
    if application.job_queue is None:
        logger.warning("JobQueue недоступен. Ежедневная проверка отключена.")
        return

    application.job_queue.run_repeating(
        scheduled_update,
        interval=UPDATE_INTERVAL_SECONDS,
        first=UPDATE_INTERVAL_SECONDS,
        name="daily_phrases_update",
    )


def build_application() -> Application:
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        raise RuntimeError("Заполни BOT_TOKEN в файле .env")

    application = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        CallbackQueryHandler(generate_phrase, pattern="^generate_phrase$")
    )
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), check_answer)
    )

    return application


def run() -> None:
    application = build_application()
    application.run_polling()
