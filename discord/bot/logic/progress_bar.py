import math
from typing import Literal

from bot.models.data import Data, Emojis


def make_progress_bar(
    d: Data,
    percent: float,
    width: int,
    palette_name: Literal["red", "purple", "green"],
) -> str:
    pallete: Emojis.ProgressBarEmojis.ProgressBarSetEmojis = getattr(
        d.emojis.progress_bar,
        palette_name,
    )

    full_count = int(percent * width) - 1
    empty_count = width - full_count - 1

    result = (pallete.middle * full_count) + (d.emojis.progress_bar.empty.middle * empty_count)

    if empty_count <= 0:
        result += pallete.right
    else:
        result += d.emojis.progress_bar.empty.right

    if full_count <= 0:
        result = d.emojis.progress_bar.empty.left + result
    else:
        result = pallete.left + result

    return result


def make_health_bar(health: int, max_health: int, full: str, half: str, empty: str):
    assert max_health % 2 == 0

    return (
        (full * (health // 2))
        + (half * (health % 2))
        + (empty * ((max_health // 2) - math.ceil(health / 2)))
        + f" ({health}/{max_health})"
    )
