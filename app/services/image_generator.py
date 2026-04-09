import inspect
import random
from difflib import SequenceMatcher
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


def build_shuffled_parts(phrase: str) -> list[dict]:
    """
    Возвращает список словарей:
    {"text": <кусок>, "word_index": 0|1}

    Важно:
    - никаких дополнительных склеек после shuffle
    - нормализация кусков делается только ДО shuffle
    """
    first_word, second_word = phrase.split()
    originals = (first_word.upper(), second_word.upper())
    dic = pyphen.Pyphen(lang="ru")

    first_parts = split_into_syllables(first_word, dic)
    second_parts = split_into_syllables(second_word, dic)

    base_parts = [{"text": part, "word_index": 0} for part in first_parts] + [
        {"text": part, "word_index": 1} for part in second_parts
    ]
    base_texts = [item["text"] for item in base_parts]

    if len(base_parts) < 4:
        shuffled = base_parts[:]
        random.shuffle(shuffled)
        return shuffled

    for _ in range(400):
        shuffled = base_parts[:]
        random.shuffle(shuffled)

        shuffled_texts = [item["text"] for item in shuffled]

        if shuffled_texts == base_texts:
            continue

        if contains_original_word_in_any_split(shuffled_texts, originals):
            continue

        sep = max(1, len(shuffled_texts) // 2)
        fake_word_1 = "".join(shuffled_texts[:sep])
        fake_word_2 = "".join(shuffled_texts[sep:])

        if not fake_word_1 or not fake_word_2:
            continue

        if looks_like_original(fake_word_1, originals):
            continue
        if looks_like_original(fake_word_2, originals):
            continue

        return shuffled

    shuffled = base_parts[:]
    random.shuffle(shuffled)
    return shuffled


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
) -> list[list[dict]]:
    """
    Делит части на 2 строки.

    Правило:
    в каждой строке должны быть части обоих слов.
    """
    if len(parts) <= 1:
        return [parts, []]

    valid_splits: list[tuple[int, int]] = []

    for index in range(1, len(parts)):
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


def render_phrase_image(phrase: str, user_id: int) -> Path:
    parts = build_shuffled_parts(phrase)

    width = 1000
    height = 400
    image = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(image)

    main_font = ImageFont.truetype(str(FONT_MAIN_PATH), 96)
    lines = split_for_balanced_lines(draw, parts, main_font)
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

    for parts_line, y in zip(non_empty_lines, y_positions, strict=False):
        widths, total_width = measure_parts(draw, parts_line, main_font)
        x = int((width - total_width) / 2)

        line_colors = random.sample(COLORS, k=min(len(parts_line), len(COLORS)))
        if len(parts_line) > len(COLORS):
            line_colors.extend(
                random.choice(COLORS) for _ in range(len(parts_line) - len(COLORS))
            )
        random.shuffle(line_colors)

        for index, part in enumerate(parts_line):
            draw.text((x, y), part["text"], fill=line_colors[index], font=main_font)
            x += widths[index]

    image_path = get_phrase_image_path(user_id)
    image.save(image_path)
    return image_path
