import datetime
import json
from typing import Any

import arrow


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):  # add support for sets
            return {"__set_object": list(obj)}

        if isinstance(obj, datetime.datetime):
            return {"__datetime_object": obj.isoformat()}

        if isinstance(obj, arrow.Arrow):
            return {"__arrow_object": obj.isoformat()}

        return json.JSONEncoder.default(self, obj)


def special_obj_hook(dct):
    if "__set_object" in dct:
        return set(dct["__set_object"])

    if "__datetime_object" in dct:
        return arrow.get(dct["__datetime_object"]).datetime

    if "__arrow_object" in dct:
        return arrow.get(dct["__arrow_object"])

    return dct


def dumps(*args, **kwargs) -> str:
    return json.dumps(*args, **kwargs, cls=CustomJSONEncoder)


def loads(*args, **kwargs) -> Any:
    return json.loads(*args, **kwargs, object_hook=special_obj_hook)
