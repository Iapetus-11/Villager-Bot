from typing import Generator, Sequence, TypeVar


T = TypeVar("T")


def chunk_sequence(sequence: Sequence[T], chunk_size: int) -> Generator[Sequence[T], None, None]:
    """Yield successive chunks from the passed sequence."""

    for i in range(0, len(sequence), chunk_size):
        yield sequence[i: i + chunk_size]
