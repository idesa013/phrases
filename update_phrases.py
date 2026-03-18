from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Final

import requests
from bs4 import BeautifulSoup

BASE_DIR: Final[Path] = Path(__file__).resolve().parent
DATA_FILE: Final[Path] = BASE_DIR / 'data' / 'phrases.json'
WIKTIONARY_URL: Final[str] = (
    'https://ru.wiktionary.org/wiki/'
    'Приложение:Список_фразеологизмов_русского_языка'
)


def normalize_phrase(value: str) -> str:
    """Нормализовать строку с фразой."""
    value = value.replace('ё', 'е').replace('Ё', 'Е')
    value = re.sub(r'[^\w\s-]', ' ', value, flags=re.UNICODE)
    value = re.sub(r'[_-]+', ' ', value)
    value = re.sub(r'\s+', ' ', value).strip().lower()
    return value


def load_local_phrases() -> list[str]:
    """Загрузить текущие локальные фразы."""
    data = json.loads(DATA_FILE.read_text(encoding='utf-8'))
    return [normalize_phrase(item) for item in data if isinstance(item, str)]


def load_phrases_from_wiktionary() -> list[str]:
    """Скачать и извлечь фразы из открытого списка Викисловаря."""
    response = requests.get(WIKTIONARY_URL, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.select_one('#mw-content-text')
    if content is None:
        return []

    phrases: list[str] = []
    for link in content.select('a'):
        text = normalize_phrase(link.get_text(' ', strip=True))
        if not text:
            continue
        if len(text.split()) < 2:
            continue
        if len(text) < 6:
            continue
        if text not in phrases:
            phrases.append(text)
    return phrases


def main() -> None:
    """Обновить локальную базу фраз."""
    local_phrases = load_local_phrases()
    remote_phrases = load_phrases_from_wiktionary()
    combined = sorted(set(local_phrases) | set(remote_phrases))
    DATA_FILE.write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Готово. Локально было: {len(local_phrases)}. С сайта получено: {len(remote_phrases)}. Итого: {len(combined)}.')


if __name__ == '__main__':
    main()
