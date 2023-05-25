from unittest.mock import MagicMock

import pytest

from common.utils.misc import today_within_date_range


@pytest.mark.parametrize(
    ("date", "expected"),
    [
        (MagicMock(month=0, day=13), False),
        (MagicMock(month=1, day=11), False),
        (MagicMock(month=1, day=12), True),
        (MagicMock(month=1, day=13), True),
        (MagicMock(month=2, day=7), True),
        (MagicMock(month=2, day=8), True),
        (MagicMock(month=2, day=9), False),
        (MagicMock(month=3, day=7), False),
    ],
)
def test_today_within_date_range(monkeypatch, date, expected):
    monkeypatch.setattr("common.utils.misc.date", MagicMock(today=MagicMock(return_value=date)))

    assert today_within_date_range(((1, 12), (2, 8))) is expected
