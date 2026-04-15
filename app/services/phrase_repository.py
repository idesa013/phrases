import json
import logging
import random

from app.config import PHRASES_PATH
from app.services.image_generator import is_phrase_shuffleable

logger = logging.getLogger(__name__)


def load_phrases() -> list[str]:
    try:
        with PHRASES_PATH.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except FileNotFoundError:
        logger.warning("Файл фраз не найден: %s", PHRASES_PATH)
        return []
    except (json.JSONDecodeError, OSError) as error:
        logger.warning("Не удалось прочитать файл фраз: %s", error)
        return []

    if isinstance(payload, list):
        return [str(item) for item in payload]

    logger.warning("Некорректный формат файла фраз: ожидался список")
    return []


def save_phrases(phrases: list[str]) -> None:
    PHRASES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PHRASES_PATH.open("w", encoding="utf-8") as file:
        json.dump(sorted(set(phrases)), file, ensure_ascii=False, indent=2)


def get_random_phrase(exclude: str | None = None) -> str:
    phrases = load_phrases()

    if not phrases:
        raise ValueError("Список фраз пуст.")

    candidates = phrases
    if exclude is not None and len(phrases) > 1:
        candidates = [phrase for phrase in phrases if phrase != exclude]

    shuffled_candidates = candidates[:]
    random.shuffle(shuffled_candidates)

    for phrase in shuffled_candidates[:100]:
        if is_phrase_shuffleable(phrase):
            return phrase

    filtered = [phrase for phrase in shuffled_candidates if is_phrase_shuffleable(phrase)]

    if not filtered:
        raise ValueError("Нет фраз, которые можно безопасно перемешать.")

    return random.choice(filtered)
