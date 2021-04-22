from bs4 import BeautifulSoup as bs
import classyjson as cj
import asyncio
import discord
import random
import arrow
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
    cdef str time = ""

    seconds -= round((hours * 60 * 60) + (minutes * 60), 2)

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

# get a lang for a given ctx object
cpdef object get_lang(_bot: object, ctx: object):
    if getattr(ctx, "guild", None) is None:
        return _bot.langs.en

    return _bot.langs[_bot.d.lang_cache.get(ctx.guild.id, "en")]

# get a prefix for a given ctx object
cpdef str get_prefix(_bot: object, ctx: object):
    if getattr(ctx, "guild", None) is None:
        return _bot.d.default_prefix

    return _bot.d.prefix_cache.get(ctx.guild.id, _bot.d.default_prefix)

async def send_tip(ctx):
    await asyncio.sleep(1)
    await ctx.send(f"{random.choice(ctx.l.misc.tip_intros)} {random.choice(ctx.l.misc.tips)}")

cpdef bint check_global(bot: object, ctx: object):
    # if bot is locked down to only accept commands from owner
    if bot.owner_locked and ctx.author.id != 536986067140608041:
        ctx.custom_err = "ignore"
    elif ctx.author.id in bot.d.ban_cache:  # if command author is bot banned
        ctx.custom_err = "bot_banned"
    elif not bot.is_ready():  # if bot hasn't completely started up yet
        ctx.custom_err = "not_ready"
    elif ctx.guild is not None and ctx.command.name in bot.d.disabled_cmds.get(
        ctx.guild.id, tuple()
    ):  # if command is disabled
        ctx.custom_err = "disabled"

    if hasattr(ctx, "custom_err"):
        return False

    # update the leaderboard + session command count
    try:
        bot.d.cmd_lb[ctx.author.id] += 1
    except KeyError:
        bot.d.cmd_lb[ctx.author.id] = 1

    bot.d.cmd_count += 1

    if ctx.command.cog and ctx.command.cog.__cog_name__ == "Econ":  # make sure it's an econ command
        if bot.d.pause_econ.get(ctx.author.id) is not None:
            ctx.custom_err = "econ_paused"
            return False

        if random.randint(1, bot.d.mob_chance) == 1:  # spawn mob
            if ctx.command._buckets._cooldown is not None and ctx.command._buckets._cooldown.per >= 2:
                bot.d.spawn_queue[ctx] = arrow.utcnow()
    elif random.randint(1, bot.d.tip_chance) == 1:
        bot.loop.create_task(send_tip(ctx))

    return True

cdef signed int lb_logic_sort_key(e: object):
    return e[1]

cpdef str lb_logic(self: object, lb_list: list, u_entry: tuple, rank_fstr: str):
    # add user entry to leaderboard if it's not there already
    if u_entry is not None and u_entry[0] not in [e[0] for e in lb_list]:
        lb_list.append(u_entry)

    # sort
    lb_list = sorted(lb_list, key=lb_logic_sort_key, reverse=True)

    # shorten list
    lb_list = lb_list[:9] if (u_entry is not None and u_entry[2] > 9) else lb_list[:10]

    cdef str body = ""
    cdef object user

    # create base leaderboard
    for entry in lb_list:
        user = self.bot.get_user(entry[0])

        if user is None:
            user = "Unknown User"
        else:
            user = discord.utils.escape_markdown(user.display_name)

        body += rank_fstr.format(entry[2], entry[1], user)

    # add user if user is missing from the leaderboard
    if u_entry is not None and u_entry[2] > 9:
        body += "\n⋮" + rank_fstr.format(
            u_entry[2], u_entry[1], discord.utils.escape_markdown(self.bot.get_user(u_entry[0]).display_name)
        )

    return body + "\uFEFF"
