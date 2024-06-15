from typing import TypedDict

from arrow import arrow


class UserQuest(TypedDict):
    key: str
    variant: int
    value: int | float
    difficulty_multi: float | None
    reward_item: str
    reward_amount: int
    day: arrow.Arrow
    done: bool
