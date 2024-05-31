import datetime
import json

import arrow
import pydantic
import pytest

from common.coms.json_encoder import special_obj_decode, special_obj_encode
from common.coms.packet import T_PACKET_DATA


@pytest.mark.parametrize(
    ("value", "serialized_value"),
    [
        ((v := {1, 2, 3}), {"__set_object": list(v)}),
        ((v := arrow.now()), {"__arrow_object": v.isoformat()}),
        ((v := datetime.datetime.now()), {"__datetime_object": v.isoformat()}),
        (
            (
                v := datetime.timedelta(
                    days=1,
                    seconds=1,
                    microseconds=1,
                    milliseconds=1,
                    minutes=1,
                    hours=1,
                    weeks=1,
                )
            ),
            {
                "__timedelta_object": {
                    "days": v.days,
                    "seconds": v.seconds,
                    "microseconds": v.microseconds,
                },
            },
        ),
    ],
)
def test_custom_object_hooks(value, serialized_value):
    class TestModel(pydantic.BaseModel):
        value: T_PACKET_DATA

        class Config:
            allow_mutation = False
            smart_union = True
            arbitrary_types_allowed = True

    serialized = TestModel(value=value).json(encoder=special_obj_encode)

    assert serialized == json.dumps({"value": serialized_value})

    model = TestModel(**json.loads(serialized, object_hook=special_obj_decode))

    assert model.value == value
