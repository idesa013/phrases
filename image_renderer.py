from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from phrase_game import PhrasePuzzle

BACKGROUND_COLOR = '#0f0f10'
TEXT_COLOR = '#f4f4f4'
ACCENT_COLORS = [
    '#ff6b6b', '#4ecdc4', '#ffe66d', '#95e06c', '#74c0fc', '#c77dff', '#ffa94d',
]


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Подобрать доступный шрифт из системных."""
    candidates = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/dejavu/DejaVuSans.ttf',
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def render_puzzle_image(puzzle: PhrasePuzzle) -> BytesIO:
    """Отрисовать изображение с перемешанными частями фразы."""
    width, height = 1200, 1200
    image = Image.new('RGB', (width, height), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    title_font = _get_font(42, bold=True)
    hint_font = _get_font(30)
    part_font = _get_font(88, bold=True)
    answer_font = _get_font(32)

    draw.text((width / 2, 70), 'Собери крылатую фразу', fill=TEXT_COLOR, anchor='mm', font=title_font)
    draw.text((width / 2, 130), 'Введи ответ сообщением в чат', fill='#bdbdbd', anchor='mm', font=hint_font)

    lines = puzzle.display_text.split('\n')
    line_y = 400
    for line in lines:
        parts = line.split()
        total_width = 0
        boxes: list[tuple[str, int]] = []
        for part in parts:
            bbox = draw.textbbox((0, 0), part, font=part_font)
            text_width = bbox[2] - bbox[0]
            boxes.append((part, text_width))
            total_width += text_width + 24
        total_width = max(0, total_width - 24)
        current_x = (width - total_width) / 2

        for index, (part, text_width) in enumerate(boxes):
            color = ACCENT_COLORS[index % len(ACCENT_COLORS)]
            draw.rounded_rectangle(
                (current_x - 18, line_y - 18, current_x + text_width + 18, line_y + 88),
                radius=24,
                outline=color,
                width=3,
            )
            draw.text((current_x, line_y), part, fill=color, font=part_font)
            current_x += text_width + 24
        line_y += 170

    draw.text((width / 2, height - 80), puzzle.phrase, fill='#6b6b6b', anchor='mm', font=answer_font)

    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer
