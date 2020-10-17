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
def make_stat_bar(value, max, slots, full, empty):
    occupado = math.floor((value / max) * slots)
    return (full * occupado) + empty * math.floor(slots - occupado)
