from bs4 import BeautifulSoup as bs
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


cpdef str make_health_bar(health: int, max_health: int, full: str, half: str, empty: str):
    assert max_health % 2 == 0

    return (
        (full * math.floor(health / 2))
        + (half * (health % 2))
        + (empty * (math.floor(max_health / 2) - math.ceil(health / 2)))
        + f" ({health}/{max_health})"
    )


cpdef str cooldown_logic(ctx: object, seconds: float):
    cdef int hours = int(seconds / 3600)
    cdef int minutes = int(seconds / 60) % 60

    seconds -= round((hours * 60 * 60) + (minutes * 60), 2)

    cdef str time = ""

    if hours == 1:
        time += f"{hours} {ctx.l.misc.time.hour}, "
    elif hours > 0:
        time += f"{hours} {ctx.l.misc.time.hours}, "

    if minutes == 1:
        time += f"{minutes} {ctx.l.misc.time.minute}, "
    elif minutes > 0:
        time += f"{minutes} {ctx.l.misc.time.minutes}, "

    if seconds == 1:
        time += f"{round(seconds, 2)} {ctx.l.misc.time.second}"
    elif seconds > 0:
        time += f"{round(seconds, 2)} {ctx.l.misc.time.seconds}"

    return time

cpdef set parse_mclists_page(page: str):
    cdef set servers_nice = set()

    cdef object soup = bs(page, "html.parser")
    cdef object elems = soup.find(class_="ui striped table servers serversa")

    if elems is None:
        return servers_nice

    elems = elems.find_all("tr")

    cdef list split
    cdef str url, ip

    for elem in elems:
        split = str(elem).split("\n")
        url = split[9][9:-2]
        ip = split[16][46:-2].replace("https://", "").replace("http://", "")

        servers_nice.add((ip, url))

    return servers_nice
