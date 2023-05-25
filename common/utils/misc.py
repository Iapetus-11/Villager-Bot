from datetime import date
from typing import Generator, Sequence, TypeVar

T = TypeVar("T")


def chunk_sequence(sequence: Sequence[T], chunk_size: int) -> Generator[Sequence[T], None, None]:
    """Yield successive chunks from the passed sequence."""

    for i in range(0, len(sequence), chunk_size):
        yield sequence[i : i + chunk_size]


def today_within_date_range(date_range: tuple[tuple[int, int], tuple[int, int]]) -> bool:
    start, end = date_range

    today = date.today()
    today_tuple = (today.month, today.day)

    return start <= today_tuple <= end
