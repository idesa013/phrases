from pathlib import Path

import matplotlib.pyplot as plt

from app.config import IMAGES_DIR


def get_statistics_image_path(user_id: int) -> Path:
    return IMAGES_DIR / f"stat_diag_{user_id}.png"


def render_statistics_chart(
    user_id: int,
    generated: int,
    right: int,
    wrong: int,
) -> Path:
    no_answer = max(0, generated - right - wrong)

    values = [right, wrong, no_answer]
    labels = ["Правильные", "Неправильные", "Без ответа"]
    colors = ["green", "red", "gray"]

    if generated == 0:
        values = [1]
        labels = ["Нет данных"]
        colors = ["gray"]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(
        values,
        labels=labels,
        colors=colors,
        autopct="%1.0f%%" if generated > 0 else None,
        startangle=90,
    )
    ax.axis("equal")

    image_path = get_statistics_image_path(user_id)
    fig.savefig(image_path, bbox_inches="tight", dpi=150)
    plt.close(fig)

    return image_path
