import datetime
import json

import arrow
import pydantic
import pytest

from common.coms.json_encoder import special_obj_decode, special_obj_encode
from common.coms.packet import T_PACKET_DATA


@pytest.mark.parametrize(
    "value,serialized_value",
    [
        ((value := {1, 2, 3}), {"__set_object": list(value)}),
        ((value := arrow.now()), {"__arrow_object": value.isoformat()}),
        ((value := datetime.datetime.now()), {"__datetime_object": value.isoformat()}),
        (
            (
                value := datetime.timedelta(
                    days=1, seconds=1, microseconds=1, milliseconds=1, minutes=1, hours=1, weeks=1
                )
            ),
            {
                "__timedelta_object": {
                    "days": value.days,
                    "seconds": value.seconds,
                    "microseconds": value.microseconds,
                }
            },
        ),
    ],
)
def test_custom_object_hooks(value, serialized_value):
    class TestModel(pydantic.BaseModel):
        value: T_PACKET_DATA

        class Config:
            arbitrary_types_allowed = True

    serialized = TestModel(value=value).json(encoder=special_obj_encode)

    print("test value:", value)
    print("serialized real:", serialized)
    print("serialized fake:", json.dumps({"value": serialized_value}))

    assert serialized == json.dumps({"value": serialized_value})

    model = TestModel(**json.loads(serialized, object_hook=special_obj_decode))

    assert model.value == value
