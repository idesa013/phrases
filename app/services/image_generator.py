import inspect
import itertools
import random
import re
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path

import pyphen
from PIL import Image, ImageDraw, ImageFont

from app.config import FONT_MAIN_PATH, IMAGES_DIR

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

COLOR_FAMILIES = {
    "#ff3b30": "red",
    "#34c759": "green",
    "#007aff": "blue",
    "#ff9500": "orange",
    "#af52de": "purple",
    "#ffd60a": "yellow",
    "#64d2ff": "blue",
    "#ff2d55": "red",
    "#30d158": "green",
    "#bf5af2": "purple",
    "#5ac8fa": "blue",
}

SHUFFLE_ATTEMPTS = 2000


class PhraseShuffleError(ValueError):
    pass


def get_phrase_image_path(user_id: int) -> Path:
    return IMAGES_DIR / f"phrase_{user_id}.png"


def split_into_syllables(word: str, dic: pyphen.Pyphen) -> list[str]:
    """
    Разбивает слово на части и нормализует односимвольные куски
    только внутри этого же слова.

    Примеры:
    ЯЗЫК -> ЯЗ | ЫК
    ЯЗЫКОВОЙ -> ЯЗ | ЫКО | ВОЙ
    """
    parts = dic.inserted(word.upper(), hyphen="•").split("•")
    parts = [part for part in parts if part]

    if not parts:
        return [word.upper()]

    # Если pyphen не разбил слово, а слово длинное,
    # запускаем нормализацию от первой буквы.
    if len(parts) == 1 and len(parts[0]) >= 4:
        parts = [parts[0][0], parts[0][1:]]

    return rebalance_single_letter_parts_in_word(parts)


def rebalance_single_letter_parts_in_word(parts: list[str]) -> list[str]:
    """
    Перебалансирует односимвольные части только внутри одного слова.

    Правило:
    если есть кусок из 1 буквы, а следующий кусок длиной 2+,
    переносим первую букву следующего куска в текущий.

    Дополнительное правило:
    если после такого переноса следующий кусок стал односимвольным,
    пытаемся подтянуть к нему первую букву следующего куска.

    Примеры:
    ["Я", "ЗЫК"] -> ["ЯЗ", "ЫК"]
    ["Я", "ЗЫ", "КО", "ВОЙ"] -> ["ЯЗ", "ЫКО", "ВОЙ"]
    """
    if len(parts) <= 1:
        return parts[:]

    result = parts[:]
    index = 0

    while index < len(result) - 1:
        current = result[index]
        next_part = result[index + 1]

        if len(current) == 1 and len(next_part) >= 2:
            moved_char = next_part[0]
            result[index] = current + moved_char
            result[index + 1] = next_part[1:]

            if (
                index + 2 < len(result)
                and len(result[index + 1]) == 1
                and len(result[index + 2]) >= 1
            ):
                moved_char_2 = result[index + 2][0]
                result[index + 1] = result[index + 1] + moved_char_2
                result[index + 2] = result[index + 2][1:]

                if not result[index + 2]:
                    result.pop(index + 2)

            if not result[index + 1]:
                result.pop(index + 1)
                continue

        index += 1

    if len(result) >= 2 and len(result[-1]) == 1:
        result[-2] += result[-1]
        result.pop()

    return [part for part in result if part]


def similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left.lower(), right.lower()).ratio()


def normalize_clue_text(text: str) -> str:
    return re.sub(r"[^а-яё]", "", text.lower())


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


def contains_original_word_in_any_split(
    parts: list[str],
    originals: tuple[str, str],
) -> bool:
    normalized_originals = {word.lower() for word in originals}

    for index in range(1, len(parts)):
        left_word = "".join(parts[:index]).lower()
        right_word = "".join(parts[index:]).lower()

        if left_word in normalized_originals:
            return True
        if right_word in normalized_originals:
            return True

    return False


def contains_original_word_in_any_run(
    parts: list[str],
    originals: tuple[str, str],
) -> bool:
    normalized_originals = {word.lower() for word in originals}

    for start in range(len(parts)):
        current = ""
        for end in range(start, len(parts)):
            current += parts[end].lower()
            if current in normalized_originals:
                return True

    return False


def contains_large_original_fragment_in_any_run(
    parts: list[str],
    originals: tuple[str, str],
) -> bool:
    normalized_originals = [normalize_clue_text(word) for word in originals]

    for start in range(len(parts)):
        current = ""
        for end in range(start, len(parts)):
            current += normalize_clue_text(parts[end])

            for original in normalized_originals:
                if not original or current == original:
                    continue

                min_clue_length = max(4, int(len(original) * 0.5))
                if len(current) >= min_clue_length and current in original:
                    return True

    return False


def _build_base_parts(phrase: str) -> tuple[list[dict], tuple[str, str]]:
    first_word, second_word = phrase.split()
    originals = (first_word.upper(), second_word.upper())
    dic = pyphen.Pyphen(lang="ru")

    first_parts = split_into_syllables(first_word, dic)
    second_parts = split_into_syllables(second_word, dic)

    base_parts = [{"text": part, "word_index": 0} for part in first_parts] + [
        {"text": part, "word_index": 1} for part in second_parts
    ]

    return base_parts, originals


def _safe_line_split_indexes(
    shuffled: list[dict],
    originals: tuple[str, str],
) -> list[int]:
    shuffled_texts = [item["text"] for item in shuffled]
    split_indexes: list[int] = []

    for index in range(1, len(shuffled_texts)):
        left = shuffled[:index]
        right = shuffled[index:]

        if {part["word_index"] for part in left} != {0, 1}:
            continue
        if {part["word_index"] for part in right} != {0, 1}:
            continue

        fake_word_1 = "".join(shuffled_texts[:index])
        fake_word_2 = "".join(shuffled_texts[index:])

        if looks_like_original(fake_word_1, originals):
            continue
        if looks_like_original(fake_word_2, originals):
            continue

        split_indexes.append(index)

    return split_indexes


def _is_valid_shuffle(
    shuffled: list[dict],
    base_texts: list[str],
    originals: tuple[str, str],
) -> bool:
    shuffled_texts = [item["text"] for item in shuffled]

    if shuffled_texts == base_texts:
        return False

    if contains_original_word_in_any_split(shuffled_texts, originals):
        return False

    if contains_original_word_in_any_run(shuffled_texts, originals):
        return False

    if contains_large_original_fragment_in_any_run(shuffled_texts, originals):
        return False

    return bool(_safe_line_split_indexes(shuffled, originals))


def build_shuffled_parts(phrase: str) -> list[dict]:
    """
    Возвращает список словарей:
    {"text": <кусок>, "word_index": 0|1}

    Важно:
    - никаких дополнительных склеек после shuffle
    - нормализация кусков делается только ДО shuffle
    """
    base_parts, originals = _build_base_parts(phrase)
    base_texts = [item["text"] for item in base_parts]

    if len(base_parts) < 4:
        raise PhraseShuffleError("Недостаточно частей для перемешивания фразы.")

    for _ in range(SHUFFLE_ATTEMPTS):
        shuffled = base_parts[:]
        random.shuffle(shuffled)

        if _is_valid_shuffle(shuffled, base_texts, originals):
            return shuffled

    if len(base_parts) <= 8:
        seen_orders: set[tuple[str, ...]] = set()

        for permutation in itertools.permutations(base_parts):
            order = tuple(item["text"] for item in permutation)
            if order in seen_orders:
                continue
            seen_orders.add(order)

            shuffled = list(permutation)
            if _is_valid_shuffle(shuffled, base_texts, originals):
                return shuffled

    raise PhraseShuffleError("Не удалось безопасно перемешать фразу.")


@lru_cache(maxsize=4096)
def is_phrase_shuffleable(phrase: str) -> bool:
    try:
        build_shuffled_parts(phrase)
    except (PhraseShuffleError, ValueError):
        return False
    return True


def measure_parts(
    draw: ImageDraw.ImageDraw,
    parts: list[dict],
    font: ImageFont.FreeTypeFont,
) -> tuple[list[int], int]:
    widths: list[int] = []

    for part in parts:
        box = draw.textbbox((0, 0), part["text"], font=font)
        widths.append(box[2] - box[0] + 18)

    return widths, sum(widths)


def split_for_balanced_lines(
    draw: ImageDraw.ImageDraw,
    parts: list[dict],
    font: ImageFont.FreeTypeFont,
    originals: tuple[str, str] | None = None,
) -> list[list[dict]]:
    """
    Делит части на 2 строки.

    Правило:
    в каждой строке должны быть части обоих слов.
    """
    if len(parts) <= 1:
        return [parts, []]

    valid_splits: list[tuple[int, int]] = []
    safe_split_indexes = None
    if originals is not None:
        safe_split_indexes = set(_safe_line_split_indexes(parts, originals))

    for index in range(1, len(parts)):
        if safe_split_indexes is not None and index not in safe_split_indexes:
            continue

        left = parts[:index]
        right = parts[index:]

        left_words = {part["word_index"] for part in left}
        right_words = {part["word_index"] for part in right}

        if left_words != {0, 1}:
            continue
        if right_words != {0, 1}:
            continue

        _, left_width = measure_parts(draw, left, font)
        _, right_width = measure_parts(draw, right, font)
        diff = abs(left_width - right_width)

        valid_splits.append((index, diff))

    if valid_splits:
        best_split = min(valid_splits, key=lambda item: item[1])[0]
        return [parts[:best_split], parts[best_split:]]

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


def _pick_part_colors(lines: list[list[dict]]) -> list[list[str]]:
    picked_lines: list[list[str]] = []
    recent_families: list[str] = []

    for line in lines:
        line_colors: list[str] = []

        for _ in line:
            blocked_families = set(recent_families[-2:])
            used_in_line = set(line_colors)
            candidates = [
                color
                for color in COLORS
                if COLOR_FAMILIES[color] not in blocked_families
                and color not in used_in_line
            ]

            if not candidates:
                candidates = [
                    color
                    for color in COLORS
                    if COLOR_FAMILIES[color] not in blocked_families
                ]

            if not candidates:
                candidates = COLORS[:]

            color = random.choice(candidates)
            line_colors.append(color)
            recent_families.append(COLOR_FAMILIES[color])

        picked_lines.append(line_colors)

    return picked_lines


def render_phrase_image(phrase: str, user_id: int) -> Path:
    parts = build_shuffled_parts(phrase)
    _, originals = _build_base_parts(phrase)

    width = 1000
    height = 400
    image = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(image)

    main_font = ImageFont.truetype(str(FONT_MAIN_PATH), 96)
    lines = split_for_balanced_lines(draw, parts, main_font, originals)
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

    colors_by_line = _pick_part_colors(non_empty_lines)

    for parts_line, line_colors, y in zip(
        non_empty_lines,
        colors_by_line,
        y_positions,
        strict=False,
    ):
        widths, total_width = measure_parts(draw, parts_line, main_font)
        x = int((width - total_width) / 2)

        for index, part in enumerate(parts_line):
            draw.text((x, y), part["text"], fill=line_colors[index], font=main_font)
            x += widths[index]

    image_path = get_phrase_image_path(user_id)
    image.save(image_path)
    return image_path
