import datetime
from typing import Any

import arrow
import pydantic.json


def special_obj_encode(obj: object) -> dict[str, Any]:
    if isinstance(obj, set):  # add support for sets
        return {"__set_object": list(obj)}

    if isinstance(obj, arrow.Arrow):
        return {"__arrow_object": obj.isoformat()}

    # due to the way Pydantic decodes types, this is necessary
    if isinstance(obj, datetime.datetime):
        return {"__datetime_object": obj.isoformat()}

    if isinstance(obj, datetime.timedelta):
        return {
            "__timedelta_object": {
                "days": obj.days,
                "seconds": obj.seconds,
                "microseconds": obj.microseconds,
            }
        }

    return pydantic.json.pydantic_encoder(obj)


def special_obj_decode(dct: dict) -> dict | Any:
    if "__set_object" in dct:
        return set(dct["__set_object"])

    if "__arrow_object" in dct:
        return arrow.get(dct["__arrow_object"])

    # due to the way Pydantic decodes types, this is necessary
    if "__datetime_object" in dct:
        return datetime.datetime.fromisoformat(dct["__datetime_object"])

    if "__timedelta_object" in dct:
        return datetime.timedelta(
            days=dct["days"], seconds=dct["seconds"], microseconds=dct["microseconds"]
        )

    return dct
