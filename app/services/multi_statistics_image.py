from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUTPUT_DIR = Path("generated")
OUTPUT_DIR.mkdir(exist_ok=True)


def _get_font(
    size: int, bold: bool = False
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_candidates = []

    if bold:
        font_candidates.extend(
            [
                "C:/Windows/Fonts/arialbd.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ]
        )
    else:
        font_candidates.extend(
            [
                "C:/Windows/Fonts/arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
        )

    for font_path in font_candidates:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, size=size)

    return ImageFont.load_default()


def _safe_username(username: str | None) -> str:
    if username:
        return f"@{username}"
    return "без username"


def render_multi_statistics_image(
    game_id: int,
    total_rounds: int,
    leaderboard: list[dict],
) -> Path:
    width = 1000
    row_height = 95
    top_block_height = 220
    bottom_padding = 50
    height = top_block_height + max(1, len(leaderboard)) * row_height + bottom_padding

    image = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(image)

    title_font = _get_font(42, bold=True)
    subtitle_font = _get_font(30, bold=False)
    row_font = _get_font(33, bold=False)
    row_bold_font = _get_font(33, bold=True)

    white = "white"
    gray = "#bdbdbd"
    green = "#00c853"
    red = "#ff1744"
    panel_bg = "#161616"
    panel_alt_bg = "#1d1d1d"
    line_color = "#2f2f2f"

    # Заголовок
    draw.text((50, 35), f"Игра № {game_id}", font=title_font, fill=white)
    draw.text(
        (50, 100), f"Всего заданий: {total_rounds}", font=subtitle_font, fill=gray
    )

    # Подзаголовок
    draw.text((50, 170), "Статистика ответов игроков", font=subtitle_font, fill=white)

    y = top_block_height

    for index, item in enumerate(leaderboard, start=1):
        username = _safe_username(item.get("username"))
        right = int(item.get("right", 0))
        wrong = int(item.get("wrong", 0))

        bg = panel_bg if index % 2 else panel_alt_bg
        draw.rounded_rectangle(
            (35, y, width - 35, y + row_height - 15),
            radius=18,
            fill=bg,
        )

        draw.text((60, y + 27), f"{index}.", font=row_bold_font, fill=white)
        draw.text((115, y + 27), username, font=row_font, fill=white)

        right_text = f"Правильных: {right}"
        wrong_text = f"Неправильных: {wrong}"

        right_bbox = draw.textbbox((0, 0), right_text, font=row_font)
        wrong_bbox = draw.textbbox((0, 0), wrong_text, font=row_font)

        wrong_width = wrong_bbox[2] - wrong_bbox[0]
        right_width = right_bbox[2] - right_bbox[0]

        wrong_x = width - 70 - wrong_width
        right_x = wrong_x - 45 - right_width

        draw.text((right_x, y + 27), right_text, font=row_font, fill=green)
        draw.text((wrong_x, y + 27), wrong_text, font=row_font, fill=red)

        draw.line(
            (50, y + row_height - 15, width - 50, y + row_height - 15),
            fill=line_color,
            width=1,
        )

        y += row_height

    output_path = OUTPUT_DIR / f"multi_stat_{game_id}.png"
    image.save(output_path)
    return output_path
