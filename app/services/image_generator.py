import inspect
import random
from difflib import SequenceMatcher
from pathlib import Path

import pyphen
from PIL import Image, ImageDraw, ImageFont

from app.config import FONT_MAIN_PATH, IMAGE_PATH

if not hasattr(inspect, "getargspec"):
    inspect.getargspec = inspect.getfullargspec


COLORS = [
    "#ff3b30",
    "#34c759",
    "#007aff",
    "#ff9500",
    "#af52de",
    "#ffd60a",
    "#64d2ff",
    "#ff2d55",
    "#30d158",
    "#bf5af2",
    "#5ac8fa",
]

VOWELS = "АЕЁИОУЫЭЮЯ"
CONSONANTS = "БВГДЖЗЙКЛМНПРСТФХЦЧШЩ"


def split_into_syllables(word: str, dic: pyphen.Pyphen) -> list[str]:
    syllables = dic.inserted(word.upper(), hyphen="•").split("•")
    syllables = [part for part in syllables if part]
    result: list[str] = []
    vowels = "АЕЁИОУЫЭЮЯ"

    for item in syllables:
        if item[0] in vowels and len(item) != 2:
            result.append(item[0])
            tail = item[1:]
            if tail:
                result.append(tail)
        elif len(item) >= 2 and item[-1] in vowels and item[-2] in vowels:
            head = item[:-1]
            if head:
                result.append(head)
            result.append(item[-1])
        else:
            result.append(item)

    return [part for part in result if part]


def starts_with_two_consonants(text: str) -> bool:
    if len(text) < 2:
        return False
    return text[0] in CONSONANTS and text[1] in CONSONANTS


def rebalance_single_letter_parts(parts: list[str]) -> list[str]:
    """
    Если слог состоит из одной буквы, а следующий начинается с двух согласных,
    переносим первую согласную следующего слога к однобуквенному слогу.

    Пример:
        ["МЕ", "ТЬ", "СПЕХ", "У", "И"] -> ["МЕ", "ТЬ", "ПЕХ", "СУ", "И"]
    или
        ["МЕ", "ТЬ", "СПЕХ", "У", "И"] -> ["МЕ", "ТЬ", "СУ", "ПЕХ", "И"]
    в зависимости от позиции после shuffle.

    По твоему правилу:
        ["...","У","СПЕХ", ...] -> ["...","СУ","ПЕХ", ...]
    """
    if len(parts) < 2:
        return parts

    result = parts[:]

    for index in range(len(result) - 1):
        current_part = result[index]
        next_part = result[index + 1]

        if len(current_part) != 1:
            continue

        if not starts_with_two_consonants(next_part):
            continue

        moved_char = next_part[0]
        result[index] = moved_char + current_part
        result[index + 1] = next_part[1:]

    return [part for part in result if part]


def normalize_shuffled_parts(parts: list[str]) -> list[str]:
    normalized = parts[:]

    for _ in range(3):
        updated = rebalance_single_letter_parts(normalized)
        if updated == normalized:
            break
        normalized = updated

    return normalized


def similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left.lower(), right.lower()).ratio()


def looks_like_original(candidate: str, originals: tuple[str, str]) -> bool:
    candidate_lower = candidate.lower()

    for original in originals:
        original_lower = original.lower()

        if candidate_lower == original_lower:
            return True

        if candidate_lower in original_lower or original_lower in candidate_lower:
            return True

        if similarity(candidate_lower, original_lower) >= 0.72:
            return True

    return False


def build_shuffled_parts(phrase: str) -> list[str]:
    first_word, second_word = phrase.split()
    originals = (first_word, second_word)

    dic = pyphen.Pyphen(lang="ru")
    base_syllables = split_into_syllables(first_word, dic) + split_into_syllables(
        second_word, dic
    )

    if len(base_syllables) < 4:
        shuffled = base_syllables[:]
        random.shuffle(shuffled)
        return normalize_shuffled_parts(shuffled)

    for _ in range(80):
        shuffled = base_syllables[:]
        random.shuffle(shuffled)
        normalized = normalize_shuffled_parts(shuffled)

        sep = max(1, len(normalized) // 2)
        fake_word_1 = "".join(normalized[:sep])
        fake_word_2 = "".join(normalized[sep:])

        if not fake_word_1 or not fake_word_2:
            continue

        if looks_like_original(fake_word_1, originals):
            continue

        if looks_like_original(fake_word_2, originals):
            continue

        return normalized

    shuffled = base_syllables[:]
    random.shuffle(shuffled)
    return normalize_shuffled_parts(shuffled)


def measure_parts(
    draw: ImageDraw.ImageDraw, parts: list[str], font: ImageFont.FreeTypeFont
) -> tuple[list[int], int]:
    widths: list[int] = []

    for part in parts:
        box = draw.textbbox((0, 0), part, font=font)
        widths.append(box[2] - box[0] + 18)

    return widths, sum(widths)


def split_for_balanced_lines(
    draw: ImageDraw.ImageDraw,
    parts: list[str],
    font: ImageFont.FreeTypeFont,
) -> list[list[str]]:
    if len(parts) <= 1:
        return [parts, []]

    best_split = 1
    best_diff = None

    for index in range(1, len(parts)):
        left = parts[:index]
        right = parts[index:]

        _, left_width = measure_parts(draw, left, font)
        _, right_width = measure_parts(draw, right, font)

        diff = abs(left_width - right_width)

        if best_diff is None or diff < best_diff:
            best_diff = diff
            best_split = index

    return [parts[:best_split], parts[best_split:]]


def get_line_height(draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont) -> int:
    box = draw.textbbox((0, 0), "АБВГД", font=font)
    return box[3] - box[1]


def render_phrase_image(phrase: str) -> Path:
    syllables = build_shuffled_parts(phrase)

    width = 1000
    height = 400
    image = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(image)
    main_font = ImageFont.truetype(str(FONT_MAIN_PATH), 96)

    lines = split_for_balanced_lines(draw, syllables, main_font)
    non_empty_lines = [line for line in lines if line]

    line_height = get_line_height(draw, main_font)
    line_gap = 34
    block_height = line_height * len(non_empty_lines) + line_gap * (
        len(non_empty_lines) - 1
    )

    vertical_offset = -12
    start_y = int((height - block_height) / 2) + vertical_offset

    y_positions: list[int] = []
    current_y = start_y
    for _ in non_empty_lines:
        y_positions.append(current_y)
        current_y += line_height + line_gap

    for parts, y in zip(non_empty_lines, y_positions, strict=False):
        widths, total_width = measure_parts(draw, parts, main_font)
        x = int((width - total_width) / 2)

        line_colors = random.sample(COLORS, k=min(len(parts), len(COLORS)))
        if len(parts) > len(COLORS):
            line_colors.extend(
                random.choice(COLORS) for _ in range(len(parts) - len(COLORS))
            )
        random.shuffle(line_colors)

        for index, part in enumerate(parts):
            draw.text((x, y), part, fill=line_colors[index], font=main_font)
            x += widths[index]

    image.save(IMAGE_PATH)
    return IMAGE_PATH
