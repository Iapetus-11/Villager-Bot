import pydantic

from common.models.base import BaseModel
from common.utils.validate_return_type import validate_return_type

import pytest


class DummyModel1(BaseModel):
    a: int
    b: str


class DummyModel2(BaseModel):
    a: str
    b: int


@pytest.mark.parametrize(
    "value",
    [
        None,
        True,
        False,
        0,
        1,
        "",
        "abc",
        [],
        [1],
        {},
        {"a": 1},
        set(),
        {1,2},
        DummyModel1(a=1, b="abc"),
        DummyModel2,
    ]
)
def test_validate_return_type(value):
    @validate_return_type
    def dummy_succeed() -> (None if value is None else type(value)):
        return value

    @validate_return_type
    def dummy_fail() -> (None if value is None else type(value)):
        class Dummy:
            pass

        return Dummy

    dummy_succeed()

    with pytest.raises(pydantic.ValidationError):
        dummy_fail()


def test_validate_return_type_on_models():
    @validate_return_type
    def dummy() -> DummyModel1:
        return DummyModel2(a="abc", b=1)  # type: ignore

    with pytest.raises(pydantic.ValidationError):
        dummy()
