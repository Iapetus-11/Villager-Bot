import math

def recursive_update(obj, new):  # hOlY FUCKING SHIT this is so big brained I AM A GOD
    if isinstance(obj, dict):
        for k, v in new.items():
            obj[k] = recursive_update(obj[k], v)
    elif isinstance(obj, list):
        for i, v in enumerate(new):
            obj[i] = recursive_update(obj[i], v)
    else:
        return new

    return obj

# Slots should be 10 cause 10 hearts / 2 idk bro I just bsed this function lmao
def make_stat_bar(value, max, slots, full, empty):  # will fuck up for sure if value is negative
    occupado = math.floor((value / max) * slots)
    return (full * occupado) + empty * math.floor(slots - occupado)

def make_health_bar(health, max_health, full, half, empty):
    assert max % 2 == 0

    bar = ''

    bar += full * (health // 2)
    bar += half * (health % 2)
    bar += empty * max_health

    return bar
