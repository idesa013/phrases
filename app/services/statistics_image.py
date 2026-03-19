from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from app.config import IMAGES_DIR


def get_statistics_image_path(user_id: int) -> Path:
    return IMAGES_DIR / f"stat_diag_{user_id}.png"


def _safe_username(username: str | None) -> str:
    if not username:
        return "unknown"
    return username.lstrip("@")


def render_statistics_chart(
    user_id: int,
    username: str | None,
    generated: int,
    right: int,
    wrong: int,
) -> Path:
    no_answer = max(0, generated - right - wrong)

    values = [right, wrong, no_answer]
    colors = ["#00c853", "#ff1744", "#9e9e9e"]
    labels = ["Правильные", "Неправильные", "Без ответа"]

    if sum(values) == 0:
        values = [1]
        colors = ["#9e9e9e"]

    fig = plt.figure(figsize=(8, 10), facecolor="black")
    fig.patch.set_facecolor("black")

    # Заголовок
    username_text = _safe_username(username)
    fig.text(
        0.5,
        0.95,
        f"Статистика ответов\nпользователя @{username_text}",
        ha="center",
        va="top",
        color="#ffd600",
        fontsize=22,
        fontweight="bold",
    )

    # Диаграмма
    ax_pie = fig.add_axes([0.18, 0.34, 0.64, 0.40], facecolor="black")
    ax_pie.pie(
        values,
        colors=colors,
        startangle=90,
        counterclock=False,
        wedgeprops={"edgecolor": "black", "linewidth": 2},
    )
    ax_pie.set_aspect("equal")
    ax_pie.set_facecolor("black")

    # Белый блок с легендой и цифрами
    ax_legend = fig.add_axes([0.14, 0.16, 0.72, 0.14])
    ax_legend.set_facecolor("white")
    ax_legend.set_xlim(0, 1)
    ax_legend.set_ylim(0, 1)
    ax_legend.set_xticks([])
    ax_legend.set_yticks([])
    for spine in ax_legend.spines.values():
        spine.set_visible(False)

    rows = [
        ("#00c853", "Правильные", right),
        ("#ff1744", "Неправильные", wrong),
        ("#9e9e9e", "Без ответа", no_answer),
    ]

    y_positions = [0.72, 0.42, 0.12]

    for (color, label, value), y in zip(rows, y_positions, strict=False):
        ax_legend.add_patch(
            Rectangle(
                (0.05, y), 0.05, 0.16, facecolor=color, edgecolor="black", linewidth=0.8
            )
        )
        ax_legend.text(
            0.14,
            y + 0.08,
            f"{label}: {value}",
            va="center",
            ha="left",
            fontsize=14,
            color="black",
            fontweight="bold",
        )

    # Низ картинки
    fig.text(
        0.5,
        0.07,
        f"Всего сгенерированных фраз: {generated}",
        ha="center",
        va="center",
        color="white",
        fontsize=18,
        fontweight="bold",
    )

    image_path = get_statistics_image_path(user_id)
    fig.savefig(
        image_path,
        dpi=160,
        facecolor=fig.get_facecolor(),
        bbox_inches="tight",
        pad_inches=0.25,
    )
    plt.close(fig)

    return image_path
