from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from image_renderer import render_puzzle_image
from phrase_game import PhrasePuzzle, PhraseRepository, build_puzzle, normalize_phrase

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

BASE_DIR: Final[Path] = Path(__file__).resolve().parent
DATA_DIR: Final[Path] = BASE_DIR / 'data'
PHRASES_FILE: Final[Path] = DATA_DIR / 'phrases.json'
GENERATE_CALLBACK: Final[str] = 'generate_phrase'
SHOW_ANSWER_CALLBACK: Final[str] = 'show_answer'


@dataclass(slots=True)
class UserGameState:
    """Состояние игры одного пользователя."""

    current_puzzle: PhrasePuzzle | None = None
    attempts: int = 0
    solved: int = 0
    total: int = 0
    last_user_answer: str | None = None


STATE: dict[int, UserGameState] = {}
REPOSITORY = PhraseRepository(PHRASES_FILE)


def get_keyboard(in_game: bool = False) -> InlineKeyboardMarkup:
    """Вернуть клавиатуру бота."""
    buttons = [[InlineKeyboardButton('GENERATE phrase!', callback_data=GENERATE_CALLBACK)]]
    if in_game:
        buttons.append([InlineKeyboardButton('Показать ответ', callback_data=SHOW_ANSWER_CALLBACK)])
    return InlineKeyboardMarkup(buttons)


def get_user_state(user_id: int) -> UserGameState:
    """Получить состояние пользователя."""
    if user_id not in STATE:
        STATE[user_id] = UserGameState()
    return STATE[user_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработать команду /start."""
    user = update.effective_user
    full_name = ' '.join(part for part in [user.first_name, user.last_name] if part).strip() if user else 'игрок'
    text = (
        f'Привет, <b>{full_name or "игрок"}</b>!\n\n'
        'Идея бота сохранена: я показываю перемешанную фразу, '
        'а ты пытаешься собрать её и присылаешь ответ сообщением.\n\n'
        'Нажми кнопку ниже.'
    )
    await update.effective_chat.send_message(
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать помощь."""
    text = (
        '<b>Команды</b>\n'
        '/start — начать игру\n'
        '/help — помощь\n'
        '/phrase — новая фраза\n'
        '/skip — показать ответ и пропустить\n'
        '/stats — статистика\n'
        '/reload — перечитать phrases.json\n\n'
        'После картинки просто отправь свой вариант фразы обычным сообщением.'
    )
    await update.effective_chat.send_message(
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_keyboard(),
    )


async def send_new_puzzle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Сгенерировать и отправить новую загадку."""
    user = update.effective_user
    if user is None:
        return

    user_state = get_user_state(user.id)
    phrase = REPOSITORY.get_random_phrase(min_words=2)
    puzzle = build_puzzle(phrase)
    user_state.current_puzzle = puzzle
    user_state.attempts = 0
    user_state.total += 1

    image = render_puzzle_image(puzzle)
    caption = 'Собери фразу из частей и пришли ответ сообщением.'
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id is None:
        return

    await context.bot.send_photo(
        chat_id=chat_id,
        photo=image,
        filename='phrase.png',
        caption=caption,
        reply_markup=get_keyboard(in_game=True),
    )


async def phrase_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда для ручной генерации новой фразы."""
    await send_new_puzzle(update, context)


async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать ответ и завершить текущий раунд."""
    user = update.effective_user
    if user is None:
        return

    user_state = get_user_state(user.id)
    if user_state.current_puzzle is None:
        await update.effective_chat.send_message('Сейчас нет активной фразы.', reply_markup=get_keyboard())
        return

    answer = user_state.current_puzzle.phrase
    user_state.current_puzzle = None
    await update.effective_chat.send_message(
        text=f'Ответ: <b>{answer}</b>',
        parse_mode=ParseMode.HTML,
        reply_markup=get_keyboard(),
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать статистику пользователя."""
    user = update.effective_user
    if user is None:
        return

    state = get_user_state(user.id)
    wrong = max(state.total - state.solved, 0)
    text = (
        '<b>Твоя статистика</b>\n'
        f'Всего раундов: <b>{state.total}</b>\n'
        f'Угадано: <b>{state.solved}</b>\n'
        f'Не угадано/пропущено: <b>{wrong}</b>\n'
        f'Фраз в базе: <b>{REPOSITORY.count}</b>'
    )
    await update.effective_chat.send_message(text=text, parse_mode=ParseMode.HTML, reply_markup=get_keyboard())


async def reload_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Перечитать JSON-файл с фразами."""
    REPOSITORY.reload()
    await update.effective_chat.send_message(
        text=f'phrases.json перечитан. Сейчас в базе <b>{REPOSITORY.count}</b> фраз.',
        parse_mode=ParseMode.HTML,
        reply_markup=get_keyboard(),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработать нажатия inline-кнопок."""
    query = update.callback_query
    if query is None:
        return

    await query.answer()

    if query.data == GENERATE_CALLBACK:
        await send_new_puzzle(update, context)
        return

    if query.data == SHOW_ANSWER_CALLBACK:
        user = update.effective_user
        if user is None:
            return
        state = get_user_state(user.id)
        if state.current_puzzle is None:
            await query.message.reply_text('Сейчас нет активной фразы.')
            return
        answer = state.current_puzzle.phrase
        state.current_puzzle = None
        await query.message.reply_text(
            text=f'Ответ: <b>{answer}</b>',
            parse_mode=ParseMode.HTML,
            reply_markup=get_keyboard(),
        )


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Проверить ответ пользователя."""
    user = update.effective_user
    message = update.effective_message
    if user is None or message is None or not message.text:
        return

    state = get_user_state(user.id)
    if state.current_puzzle is None:
        await update.effective_chat.send_message(
            'Нажми кнопку и я пришлю новую фразу.',
            reply_markup=get_keyboard(),
        )
        return

    state.attempts += 1
    state.last_user_answer = message.text

    user_answer = normalize_phrase(message.text)
    correct_answer = normalize_phrase(state.current_puzzle.phrase)

    if user_answer == correct_answer:
        state.solved += 1
        solved_phrase = state.current_puzzle.phrase
        state.current_puzzle = None
        await update.effective_chat.send_message(
            text=(
                '✅ Верно!\n\n'
                f'<b>{solved_phrase}</b>\n'
                f'Попыток в раунде: <b>{state.attempts}</b>'
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=get_keyboard(),
        )
        return

    await update.effective_chat.send_message(
        text='❌ Пока не угадал. Попробуй ещё раз или нажми «Показать ответ».',
        reply_markup=get_keyboard(in_game=True),
    )


def create_application() -> Application:
    """Создать и настроить Telegram-приложение."""
    token = os.getenv('BOT_TOKEN')
    if not token:
        raise RuntimeError('Не найден BOT_TOKEN. Создай .env или задай переменную окружения.')

    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('phrase', phrase_command))
    application.add_handler(CommandHandler('skip', skip_command))
    application.add_handler(CommandHandler('stats', stats_command))
    application.add_handler(CommandHandler('reload', reload_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))
    return application


if __name__ == '__main__':
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

    app = create_application()
    logger.info('Bot is starting...')
    app.run_polling()
