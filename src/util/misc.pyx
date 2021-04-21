import classyjson as cj
import math


def recursive_update(obj, new):  # hOlY FUCKING SHIT this is so big brained I AM A GOD
    if isinstance(obj, dict) and isinstance(new, dict):
        for k, v in new.items():
            obj[k] = recursive_update(obj.get(k, cj.classify({})), v)
    elif isinstance(obj, list) and isinstance(new, list):
        obj = []  # obj here needs to be reset to zero to avoid weird list issues (see /update command in cogs/cmds/owner.py)
        for i, v in enumerate(new):
            obj.append(recursive_update(obj[i], v) if i < len(obj) else v)
    else:
        return new

    return obj


# # Slots should be 10 cause 10 hearts / 2 idk bro I just bsed this function lmao
# def make_stat_bar(value, max, slots, full, empty):  # will fuck up for sure if value is negative
#     occupado = math.floor((value / max) * slots)
#     return (full * occupado) + empty * math.floor(slots - occupado)


cpdef make_health_bar(health: int, max_health: int, full: string, half: string, empty: string):
    assert max_health % 2 == 0

    return (
        (full * math.floor(health / 2.0))
        + (half * (health % 2.0))
        + (empty * (math.floor(max_health / 2.0) - math.ceil(health / 2.0)))
        + f" ({health}/{max_health})"
    )
