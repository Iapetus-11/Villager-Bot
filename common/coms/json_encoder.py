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

    return pydantic.json.pydantic_encoder(obj)


def special_obj_decode(dct: dict) -> dict | Any:
    if val := dct.get("__set_object"):
        return set(val)

    if val := dct.get("__arrow_object"):
        return arrow.get(val)

    # due to the way Pydantic decodes types, this is necessary
    if val := dct.get("__datetime_object"):
        return datetime.datetime.fromisoformat(val)

    return dct
