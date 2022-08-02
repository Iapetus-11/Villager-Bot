import json
from typing import Any


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):  # add support for sets
            return {"__set_object": list(obj)}

        return json.JSONEncoder.default(self, obj)


def special_obj_hook(dct):
    if "__set_object" in dct:
        return set(dct["__set_object"])

    return dct


def dumps(*args, **kwargs) -> str:
    return json.dumps(*args, **kwargs, cls=CustomJSONEncoder)


def loads(*args, **kwargs) -> Any:
    return json.loads(*args, **kwargs, object_hook=special_obj_hook)
