from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pyphen

VOWELS: Final[set[str]] = set('аеёиоуыэюяАЕЁИОУЫЭЮЯ')


@dataclass(slots=True)
class PhrasePuzzle:
    """Игровая загадка по фразе."""

    phrase: str
    scrambled_parts: list[str]
    display_text: str


class PhraseRepository:
    """Хранилище фраз из JSON-файла."""

    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        self._phrases: list[str] = []
        self.reload()

    def reload(self) -> None:
        """Перезагрузить список фраз из файла."""
        data = json.loads(self._file_path.read_text(encoding='utf-8'))
        if not isinstance(data, list):
            raise ValueError('phrases.json должен содержать список строк.')

        phrases: list[str] = []
        for item in data:
            if not isinstance(item, str):
                continue
            phrase = normalize_phrase(item)
            if phrase and phrase not in phrases:
                phrases.append(phrase)

        if not phrases:
            raise ValueError('Список фраз пуст.')

        self._phrases = phrases

    @property
    def count(self) -> int:
        return len(self._phrases)

    def get_random_phrase(self, min_words: int = 2) -> str:
        filtered = [phrase for phrase in self._phrases if len(phrase.split()) >= min_words]
        pool = filtered or self._phrases
        return random.choice(pool)


def normalize_phrase(value: str) -> str:
    """Нормализовать фразу для хранения и сравнения."""
    value = value.replace('ё', 'е').replace('Ё', 'Е')
    value = re.sub(r'[^\w\s-]', ' ', value, flags=re.UNICODE)
    value = re.sub(r'[_-]+', ' ', value)
    value = re.sub(r'\s+', ' ', value).strip().lower()
    return value


def split_to_parts(word: str, dic: pyphen.Pyphen) -> list[str]:
    """Разбить слово на игровые части."""
    cleaned = re.sub(r'[^а-яА-ЯёЁa-zA-Z-]', '', word)
    if not cleaned:
        return []

    inserted = dic.inserted(cleaned, hyphen='•')
    parts = [part for part in inserted.split('•') if part]
    if len(parts) <= 1:
        parts = fallback_split(cleaned)
    return refine_parts(parts)


def fallback_split(word: str) -> list[str]:
    """Запасное разбиение слова на части без словаря переносов."""
    if len(word) <= 3:
        return [word]

    parts: list[str] = []
    current = ''
    for index, letter in enumerate(word):
        current += letter
        next_letter = word[index + 1] if index + 1 < len(word) else ''
        if letter in VOWELS and len(current) >= 2 and next_letter:
            parts.append(current)
            current = ''
    if current:
        parts.append(current)
    return parts or [word]


def refine_parts(parts: list[str]) -> list[str]:
    """Сделать части более удобными для чтения и игры."""
    refined: list[str] = []
    for part in parts:
        if len(part) >= 3:
            refined.append(part)
            continue

        if refined:
            refined[-1] += part
        else:
            refined.append(part)

    return refined


def build_puzzle(phrase: str) -> PhrasePuzzle:
    """Построить игровую загадку из фразы."""
    dic = pyphen.Pyphen(lang='ru_RU')
    words = phrase.split()

    parts: list[str] = []
    for word in words:
        parts.extend(split_to_parts(word, dic))

    if len(parts) < 2:
        parts = words[:]

    random.shuffle(parts)
    half = max(1, len(parts) // 2)
    first_line = ' '.join(parts[:half])
    second_line = ' '.join(parts[half:])
    display_text = first_line if not second_line else f'{first_line}\n{second_line}'

    return PhrasePuzzle(
        phrase=phrase,
        scrambled_parts=parts,
        display_text=display_text,
    )
