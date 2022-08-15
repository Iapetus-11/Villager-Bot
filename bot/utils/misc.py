import asyncio
import math
import time
from collections import defaultdict
from contextlib import suppress
from typing import Any

import discord

from common.models.db.item import Item
from common.models.db.user import User

from common.utils.code import format_exception

from datetime import timedelta
import re


DURATION_REGEX = re.compile(
    r"((?P<weeks>\d+?) ?(weeks|week|W|w) ?)?"
    r"((?P<days>\d+?) ?(days|day|D|d) ?)?"
    r"((?P<hours>\d+?) ?(hours|hour|hr|H|h) ?)?"
    r"((?P<minutes>\d+?) ?(minutes|minute|min|M|m) ?)?"
    r"((?P<seconds>\d+?) ?(seconds|second|sec|S|s))?"
)

def parse_timedelta(duration: str) -> timedelta | None:
    """
    Converts a `duration` string to a relativedelta objects.
    - weeks: `w`, `W`, `week`, `weeks`
    - days: `d`, `D`, `day`, `days`
    - hours: `H`, `h`, `hour`, `hours`
    - minutes: `m`, `min`, `minute`, `minutes`
    - seconds: `S`, `sec`, `s`, `second`, `seconds`
    The units need to be provided in descending order of magnitude.
    """

    match = DURATION_REGEX.fullmatch(duration)
    if not match:
        return None

    duration_dict = {unit: int(amount) for unit, amount in match.groupdict(default=0).items()}

    delta = timedelta(**duration_dict)

    return delta


def get_timedelta_granularity(delta: timedelta, granularity: int) -> list[str]:
    def _get_timedelta_granularity():
        if delta.days >= 365:
            yield "year"
        
        if delta.days % 365 >= 31:
            yield "month"

        if delta.days % 30 >= 7:
            yield "week"

        if delta.days % 7 >= 1:
            yield "day"

        if delta.seconds >= 3600:
            yield "hour"

        if delta.seconds % 3600 >= 60:
            yield "minute"

        if delta.seconds % 60 >= 1:
            yield "second"

    return list(_get_timedelta_granularity())[:granularity]


def strip_command(ctx):  # returns message.clean_content excluding the command used
    length = len(ctx.prefix) + len(ctx.invoked_with) + 1
    return ctx.message.clean_content[length:]


def make_health_bar(health: int, max_health: int, full: str, half: str, empty: str):
    assert max_health % 2 == 0

    return (
        (full * (health // 2))
        + (half * (health % 2))
        + (empty * ((max_health // 2) - math.ceil(health / 2)))
        + f" ({health}/{max_health})"
    )


async def _attempt_get_username(bot, user_id: int) -> str:
    # first see if current cluster has user in cache
    user_name = getattr(bot.get_user(user_id), "name", None)

    # fall back to other clusters to get username
    if user_name is None:
        user_name = await bot.karen.get_user_name(user_id)

    return user_name or "unknown user"


async def _craft_lb(bot, leaderboard: list[dict[str, Any]], row_fstr: str) -> str:
    body = ""
    last_idx = 0

    for i, row in enumerate(leaderboard):
        user_name = discord.utils.escape_markdown(await _attempt_get_username(bot, row["user_id"]))

        idxs_skipped: bool = last_idx != row["idx"] - 1

        if idxs_skipped:
            body += "\n⋮"

        if i < 9 or idxs_skipped:
            body += row_fstr.format(row["idx"], row["amount"], user_name)
            last_idx = row["idx"]

    return body + "\uFEFF"


async def craft_lbs(
    bot, global_lb: list[dict[str, Any]], local_lb: list[dict[str, Any]], row_fstr: str
) -> tuple[str, str]:
    return await asyncio.gather(
        _craft_lb(bot, global_lb, row_fstr), _craft_lb(bot, local_lb, row_fstr)
    )


def calc_total_wealth(db_user: User, items: list[Item]):
    return (
        db_user.emeralds
        + db_user.vault_balance * 9
        + sum([u_it.sell_price * u_it.amount for u_it in items if u_it.sell_price > 0])
    )


def emojify_item(d, item: str):
    try:
        emoji_key = d.emoji_items[item]

        if emoji_key.startswith("fish."):
            return d.emojis.fish[emoji_key[5:]]

        if emoji_key.startswith("farming.normal."):
            return d.emojis.farming.normal[emoji_key[15:]]

        if emoji_key.startswith("farming.seeds."):
            return d.emojis.farming.seeds[emoji_key[14:]]

        return d.emojis[emoji_key]
    except KeyError:
        return d.emojis.air


def emojify_crop(d, crop: str):
    return d.emojis.farming.growing[d.farming.emojis.growing[crop]]


def format_required(d: object, shop_item: object, amount: int = 1):
    base = f" {shop_item.buy_price * amount}{d.emojis.emerald}"

    for req_item, req_amount in shop_item.requires.get("items", {}).items():
        base += f" + {req_amount * amount}{d.emojis[d.emoji_items[req_item]]}"

    return base


async def update_support_member_role(bot, member):
    try:
        db = bot.get_cog("Database")

        support_guild = bot.get_guild(bot.d.support_server_id)

        if support_guild is None:
            support_guild = await bot.fetch_guild(bot.d.support_server_id)

        role_map_values = set(bot.d.role_mappings.values())

        roles = []

        for role in member.roles:  # add non rank roles to roles list
            if role.id not in role_map_values and role.id != bot.d.support_server_id:
                roles.append(role)

        pickaxe_role = bot.d.role_mappings.get(await db.fetch_pickaxe(member.id))
        if pickaxe_role is not None:
            roles.append(support_guild.get_role(pickaxe_role))

        if await db.fetch_item(member.id, "Bane Of Pillagers Amulet") is not None:
            roles.append(support_guild.get_role(bot.d.role_mappings.get("BOP")))

        if roles != member.roles:
            try:
                await member.edit(roles=roles)
            except discord.errors.HTTPException:
                pass
    except Exception as e:
        print(format_exception(e))


class TTLPreventDuplicate:
    def __init__(self, expire_after: float):
        self.expire_after = expire_after

        self.store = {}

    def put(self, obj):
        self.store[obj] = time.time()

    def check(self, obj):
        return obj in self.store

    def clear_dead(self) -> None:
        for k, v in list(self.store.items()):
            if (time.time() - v) > self.expire_after:
                del self.store[k]


def fix_giphy_url(url: str) -> str:
    return f"https://i.giphy.com/media/{url.split('-')[-1]}/giphy.gif"


class SuppressCtxManager:
    def __init__(self, manager):
        self._manager = manager

    def __enter__(self):
        with suppress(Exception):
            self._manager.__enter__()

    def __exit__(self, *args, **kwargs):
        with suppress(Exception):
            self._manager.__exit__(*args, **kwargs)

    async def __aenter__(self):
        with suppress(Exception):
            await self._manager.__aenter__()

    async def __aexit__(self, *args, **kwargs):
        with suppress(Exception):
            await self._manager.__aexit__(*args, **kwargs)


class MultiLock:
    def __init__(self):
        self._locks = defaultdict(asyncio.Lock)

    async def acquire(self, ids: list) -> None:
        await asyncio.wait([self._locks[i].acquire() for i in ids])

    def release(self, ids: list) -> None:
        for i in ids:
            self._locks[i].release()

    def locked(self, ids: list) -> bool:
        return any([self._locks[i].locked() for i in ids])


def chunk_by_lines(text: str, max_paragraph_size: int) -> str:
    text_lines = text.splitlines()

    for line in text_lines:
        if len(line) > max_paragraph_size:
            raise ValueError("A singular line may not exceed max_paragraph_size.")

    paragraph = []

    for line in text.splitlines():
        if sum(len(l) for l in paragraph) + len(line) > max_paragraph_size:
            yield "\n".join(paragraph)
            paragraph.clear()

        paragraph.append(line)

    if paragraph:
        yield "\n".join(paragraph)


class CommandOnKarenCooldown(Exception):
    def __init__(self, remaining: float):
        self.remaining = remaining


class MaxKarenConcurrencyReached(Exception):
    pass
