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

def make_health_bar(health, max_health, full, half, empty):
    assert max_health % 2 == 0
    return (full * (health // 2)) + (half * (health % 2)) + (empty * (max_health // 2 - (health // 2)))

def make_health_bar_debug(health, max_health, full, half, empty):
    assert max_health % 2 == 0
    return (full * (health // 2)) + (half * (health % 2)) + (empty * (max_health // 2 - (health // 2))) + f' ({health}/{max_health})'

def insert_returns(body: str):
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)
        
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)
