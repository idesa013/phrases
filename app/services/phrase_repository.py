import json
import random

from app.config import PHRASES_PATH


def load_phrases() -> list[str]:
    with PHRASES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_phrases(phrases: list[str]) -> None:
    PHRASES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PHRASES_PATH.open("w", encoding="utf-8") as file:
        json.dump(sorted(set(phrases)), file, ensure_ascii=False, indent=2)


def get_random_phrase(exclude: str | None = None) -> str:
    phrases = load_phrases()

    if not phrases:
        raise ValueError("Список фраз пуст.")

    if exclude is None or len(phrases) == 1:
        return random.choice(phrases)

    filtered = [phrase for phrase in phrases if phrase != exclude]

    if not filtered:
        return random.choice(phrases)

    return random.choice(filtered)
