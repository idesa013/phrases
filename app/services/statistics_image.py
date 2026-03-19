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

    # Порядок только для легенды/чисел
    green = "#00c853"
    red = "#ff1744"
    gray = "#9e9e9e"

    # Порядок именно для круга:
    # слева сверху зелёный -> справа красный -> снизу/снизу-слева серый
    pie_values = [right, wrong, no_answer]
    pie_colors = [green, red, gray]

    if sum(pie_values) == 0:
        pie_values = [1]
        pie_colors = [gray]

    fig = plt.figure(figsize=(7.2, 8.4), facecolor="black")
    fig.patch.set_facecolor("black")

    username_text = _safe_username(username)

    # Заголовок — чуть выше и компактнее
    fig.text(
        0.5,
        0.93,
        f"Статистика ответов\nпользователя @{username_text}",
        ha="center",
        va="top",
        color="#ffd600",
        fontsize=21,
        fontweight="bold",
    )

    # Круг — больше и выше
    ax_pie = fig.add_axes([0.05, 0.24, 0.90, 0.60], facecolor="black")
    radius = 1.12
    wedges, texts, autotexts = ax_pie.pie(
        pie_values,
        colors=pie_colors,
        startangle=200,  # <-- чтобы зелёный ушёл влево-вверх, красный вправо
        counterclock=False,  # <-- порядок по часовой стрелке
        autopct="%1.0f%%" if generated > 0 else None,
        pctdistance=0.56,
        wedgeprops={"edgecolor": "black", "linewidth": 2.2},
        textprops={"color": "black", "fontsize": 22, "fontweight": "bold"},
    )
    ax_pie.set_aspect("equal")
    ax_pie.set_facecolor("black")

    for text in texts:
        text.set_visible(False)

    # Нижние блоки — как на скрине, шире и ближе к низу
    left_box = fig.add_axes([0.09, 0.06, 0.40, 0.10])
    right_box = fig.add_axes([0.52, 0.06, 0.40, 0.10])

    for ax in (left_box, right_box):
        ax.set_facecolor("white")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    # Левый белый блок
    left_box.add_patch(
        Rectangle(
            (0.05, 0.56), 0.10, 0.22, facecolor=green, edgecolor="black", linewidth=0.6
        )
    )
    left_box.text(
        0.23,
        0.67,
        f"Правильные: {right}",
        ha="left",
        va="center",
        fontsize=14,
        color="black",
        fontweight="bold",
    )

    left_box.add_patch(
        Rectangle(
            (0.05, 0.14), 0.10, 0.22, facecolor=red, edgecolor="black", linewidth=0.6
        )
    )
    left_box.text(
        0.23,
        0.25,
        f"Неправильные: {wrong}",
        ha="left",
        va="center",
        fontsize=14,
        color="black",
        fontweight="bold",
    )

    # Правый белый блок
    right_box.add_patch(
        Rectangle(
            (0.05, 0.56), 0.10, 0.22, facecolor=gray, edgecolor="black", linewidth=0.6
        )
    )
    right_box.text(
        0.23,
        0.67,
        f"Без ответа: {no_answer}",
        ha="left",
        va="center",
        fontsize=14,
        color="black",
        fontweight="bold",
    )

    right_box.text(
        0.5,
        0.25,
        f"Всего фраз: {generated}",
        ha="center",
        va="center",
        fontsize=14,
        color="black",
        fontweight="bold",
    )

    image_path = get_statistics_image_path(user_id)
    fig.savefig(
        image_path,
        dpi=160,
        facecolor="black",
        # bbox_inches="tight",
        pad_inches=0.08,
    )
    plt.close(fig)

    return image_path
