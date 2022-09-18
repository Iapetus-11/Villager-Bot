from typing import Any

import arrow
import pydantic.json


def special_obj_encode(obj: object) -> dict[str, Any]:
    if isinstance(obj, set):  # add support for sets
        return {"__set_object": list(obj)}

    if isinstance(obj, arrow.Arrow):
        return {"__arrow_object": obj.isoformat()}

    return pydantic.json.pydantic_encoder(obj)


def special_obj_decode(dct: dict) -> dict | Any:
    if "__set_object" in dct:
        return set(dct["__set_object"])

    if "__arrow_object" in dct:
        return arrow.get(dct["__arrow_object"])

    return dct
