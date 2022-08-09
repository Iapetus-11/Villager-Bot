import asyncio
import math
import time
from collections import defaultdict
from contextlib import suppress
from typing import Any, List, Tuple

import arrow
import discord

from common.models.db.item import Item
from common.models.db.user import User

from common.utils.code import format_exception


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


async def _craft_lb(bot, leaderboard: List[dict[str, Any]], row_fstr: str) -> str:
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
    bot, global_lb: List[dict[str, Any]], local_lb: List[dict[str, Any]], row_fstr: str
) -> Tuple[str, str]:
    return await asyncio.gather(
        _craft_lb(bot, global_lb, row_fstr), _craft_lb(bot, local_lb, row_fstr)
    )


def calc_total_wealth(db_user: User, items: List[Item]):
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


def parse_input_time(args: List[str]) -> Tuple[bool, arrow.Arrow, str]:
    at = arrow.utcnow()
    i = 0

    try:
        for i, arg in enumerate(args):
            if arg.endswith("m"):
                at = at.shift(minutes=int(arg[:-1]))
            elif arg.endswith("minute"):
                at = at.shift(minutes=int(arg[:-6]))
            elif arg.endswith("minutes"):
                at = at.shift(minutes=int(arg[:-7]))
            elif arg.endswith("h"):
                at = at.shift(hours=int(arg[:-1]))
            elif arg.endswith("hour"):
                at = at.shift(hours=int(arg[:-4]))
            elif arg.endswith("hours"):
                at = at.shift(hours=int(arg[:-5]))
            elif arg.endswith("d"):
                at = at.shift(days=int(arg[:-1]))
            elif arg.endswith("day"):
                at = at.shift(days=int(arg[:-3]))
            elif arg.endswith("days"):
                at = at.shift(days=int(arg[:-4]))
            elif arg.endswith("w"):
                at = at.shift(weeks=int(arg[:-1]))
            elif arg.endswith("week"):
                at = at.shift(weeks=int(arg[:-4]))
            elif arg.endswith("weeks"):
                at = at.shift(weeks=int(arg[:-5]))
            else:
                break
    except ValueError:
        pass

    if i == 0:
        return (False, at, " ".join(args[i:]))

    return (True, at, " ".join(args[i:]))


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
