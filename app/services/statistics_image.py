from pathlib import Path
from math import cos, sin, radians

from PIL import Image, ImageDraw, ImageFont

from app.config import FONT_HINT_BOLD_PATH, FONT_HINT_PATH, IMAGES_DIR


WIDTH = 900
HEIGHT = 1100

BLACK = "#000000"
WHITE = "#FFFFFF"
YELLOW = "#FFD600"
GREEN = "#00C853"
RED = "#FF1744"
GRAY = "#9E9E9E"


def get_statistics_image_path(user_id: int) -> Path:
    return IMAGES_DIR / f"stat_diag_{user_id}.png"


def _safe_username(username: str | None) -> str:
    if not username:
        return "unknown"
    return username.lstrip("@") or "unknown"


def _load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(str(path), size)
    except Exception:
        return ImageFont.load_default()


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
) -> None:
    draw.text(xy, text, font=font, fill=fill, anchor="mm")


def draw_text_with_shadow(
    draw,
    position,
    text,
    font,
    fill,
    shadow_color=(220, 0, 0),
    shadow_offset=(2, 2),
):
    x, y = position

    # тень
    draw.text(
        (x + shadow_offset[0], y + shadow_offset[1]),
        text,
        font=font,
        fill=shadow_color,
    )

    # основной текст
    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
    )


def _draw_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str,
) -> None:
    draw.rounded_rectangle(box, radius=0, fill=fill)


def _draw_legend_square(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    color: str,
) -> None:
    draw.rectangle((x, y, x + 34, y + 34), fill=color, outline="black", width=1)


def _draw_pie_slice(
    draw: ImageDraw.ImageDraw,
    bbox: tuple[int, int, int, int],
    start_angle: float,
    end_angle: float,
    fill: str,
) -> None:
    draw.pieslice(
        bbox, start=start_angle, end=end_angle, fill=fill, outline="black", width=4
    )


def _draw_percentage_label(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    radius: int,
    start_angle: float,
    end_angle: float,
    percent_text: str,
    font: ImageFont.FreeTypeFont,
) -> None:
    mid = (start_angle + end_angle) / 2
    label_radius = radius * 0.50
    x = center[0] + cos(radians(mid)) * label_radius
    y = center[1] + sin(radians(mid)) * label_radius
    draw.text((x, y), percent_text, font=font, fill="black", anchor="mm")


def render_statistics_chart(
    user_id: int,
    username: str | None,
    generated: int,
    right: int,
    wrong: int,
) -> Path:
    no_answer = max(0, generated - right - wrong)

    image = Image.new("RGB", (WIDTH, HEIGHT), BLACK)
    draw = ImageDraw.Draw(image)

    title_font = _load_font(FONT_HINT_BOLD_PATH, 44)
    username_font = _load_font(FONT_HINT_BOLD_PATH, 50)
    percent_font = _load_font(FONT_HINT_BOLD_PATH, 42)
    legend_font = _load_font(FONT_HINT_BOLD_PATH, 26)
    bottom_font = _load_font(FONT_HINT_BOLD_PATH, 30)

    username_text = _safe_username(username)

    title_line = "Статистика ответов пользователя"
    username_line = f"@{username_text}"

    line_spacing = 15

    # размеры строк
    bbox1 = draw.textbbox((0, 0), title_line, font=title_font)
    h1 = bbox1[3] - bbox1[1]

    bbox2 = draw.textbbox((0, 0), username_line, font=title_font)
    h2 = bbox2[3] - bbox2[1]

    total_height = h1 + h2 + line_spacing

    start_y = 110 - total_height // 2

    # --- первая строка ---
    w1 = bbox1[2] - bbox1[0]
    x1 = WIDTH // 2 - w1 // 2

    draw.text(
        (x1, start_y),
        title_line,
        font=title_font,
        fill=YELLOW,
    )

    # --- вторая строка ---
    w2 = bbox2[2] - bbox2[0]
    x2 = WIDTH // 2 - w2 // 2

    draw_text_with_shadow(
        draw,
        (x2, start_y + h1 + line_spacing),
        username_line,
        username_font if "username_font" in locals() else title_font,
        YELLOW,
    )

    # Круг
    center = (WIDTH // 2, 480)
    radius = 285
    pie_bbox = (
        center[0] - radius,
        center[1] - radius,
        center[0] + radius,
        center[1] + radius,
    )

    values = [right, wrong, no_answer]
    colors = [GREEN, RED, GRAY]

    total = sum(values)

    if total == 0:
        _draw_pie_slice(draw, pie_bbox, 0, 360, GRAY)
    else:
        # Порядок: слева сверху зелёный -> справа красный -> снизу серый
        start_angle = 180

        for value, color in zip(values, colors, strict=False):
            if value <= 0:
                continue

            angle = 360 * value / total
            end_angle = start_angle + angle
            _draw_pie_slice(draw, pie_bbox, start_angle, end_angle, color)

            percent = round(value * 100 / total)
            _draw_percentage_label(
                draw,
                center=center,
                radius=radius,
                start_angle=start_angle,
                end_angle=end_angle,
                percent_text=f"{percent}%",
                font=percent_font,
            )
            start_angle = end_angle

    # Нижние белые блоки
    left_box = (70, 810, 415, 940)
    right_box = (485, 810, 830, 940)

    _draw_box(draw, left_box, WHITE)
    _draw_box(draw, right_box, WHITE)

    _draw_legend_square(draw, 92, 830, GREEN)
    draw.text(
        (150, 847), f"Правильные: {right}", font=legend_font, fill="black", anchor="lm"
    )

    _draw_legend_square(draw, 92, 885, RED)
    draw.text(
        (150, 902),
        f"Неправильные: {wrong}",
        font=legend_font,
        fill="black",
        anchor="lm",
    )

    _draw_legend_square(draw, 507, 830, GRAY)
    draw.text(
        (565, 847),
        f"Без ответа: {no_answer}",
        font=legend_font,
        fill="black",
        anchor="lm",
    )

    draw.text(
        (657, 902),
        f"Всего фраз: {generated}",
        font=legend_font,
        fill="black",
        anchor="mm",
    )

    draw.text(
        (WIDTH // 2, 1000),
        f"Всего сгенерированных фраз: {generated}",
        font=bottom_font,
        fill="white",
        anchor="mm",
    )

    image_path = get_statistics_image_path(user_id)
    image.save(image_path)
    return image_path
