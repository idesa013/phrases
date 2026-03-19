import re


def normalize_phrase_text(text: str) -> str:
    text = text.strip().lower()
    text = text.replace("ё", "е")
    text = re.sub(r"\s+", " ", text)
    return text
