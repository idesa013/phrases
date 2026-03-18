import re


VOWELS = set("аеёиоуыэюяАЕЁИОУЫЭЮЯ")
LATIN_TO_CYRILLIC = str.maketrans(
    {
        "A": "А",
        "B": "В",
        "C": "С",
        "E": "Е",
        "H": "Н",
        "K": "К",
        "M": "М",
        "O": "О",
        "P": "Р",
        "T": "Т",
        "X": "Х",
        "Y": "У",
        "a": "а",
        "c": "с",
        "e": "е",
        "h": "н",
        "k": "к",
        "m": "м",
        "o": "о",
        "p": "р",
        "t": "т",
        "x": "х",
        "y": "у",
    }
)


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def normalize_phrase_text(text: str) -> str:
    cleaned = text.translate(LATIN_TO_CYRILLIC)
    cleaned = cleaned.replace("—", "-").replace("–", "-")
    cleaned = normalize_whitespace(cleaned)
    return cleaned


def normalize_answer(text: str) -> str:
    cleaned = normalize_phrase_text(text).lower().replace("ё", "е")
    return cleaned


def count_letters(word: str) -> int:
    return sum(1 for char in word if char.isalpha())


def count_syllables(word: str) -> int:
    return sum(1 for char in word if char in VOWELS)


def is_valid_two_word_phrase(phrase: str) -> bool:
    parts = normalize_phrase_text(phrase).split()
    if len(parts) != 2:
        return False

    return all(
        count_letters(word) >= 4 and count_syllables(word) >= 2
        for word in parts
    )
