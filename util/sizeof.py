from types import ModuleType, FunctionType
from gc import get_referents
import sys

BLACKLIST = (type, ModuleType, FunctionType)


def getsize(obj):
    if isinstance(obj, BLACKLIST):
        raise TypeError("getsize() does not take argument of type: " + str(type(obj)))

    seen_ids = set()
    size = 0
    objects = [obj]

    while objects:
        need_referents = []

        for obj in objects:
            if not isinstance(obj, BLACKLIST) and id(obj) not in seen_ids:
                seen_ids.add(id(obj))
                size += sys.getsizeof(obj)
                need_referents.append(obj)

        objects = get_referents(*need_referents)

    return size
