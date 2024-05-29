import asyncio
import io
import math
import mimetypes
import re
import time
from collections import defaultdict
from contextlib import suppress
from datetime import timedelta
from typing import Any, Generator

import aiohttp
import discord

from common.models.db.item import Item
from common.models.db.user import User
from common.utils.code import format_exception


class _Sentinel:
    pass


SENTINEL = _Sentinel()


def parse_timedelta(duration: str) -> timedelta | None:
    """
    Converts a `duration` string to a relativedelta objects.
    - weeks: `w`, `W`, `week`, `weeks`
    - days: `d`, `D`, `day`, `days`
    - hours: `H`, `h`, `hour`, `hours`
    - minutes: `m`, `min`, `minute`, `minutes`
    - seconds: `S`, `sec`, `s`, `second`, `seconds`
    The units need to be provided in descending order of magnitude.

    CREDIT: This code was taken and modified from https://github.com/ClemBotProject/ClemBot
    """

    DURATION_REGEX = re.compile(
        r"((?P<weeks>\d+?) ?(weeks|week|W|w) ?)?"
        r"((?P<days>\d+?) ?(days|day|D|d) ?)?"
        r"((?P<hours>\d+?) ?(hours|hour|hr|H|h) ?)?"
        r"((?P<minutes>\d+?) ?(minutes|minute|min|M|m) ?)?"
    )

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


def clean_text(msg: discord.Message, text: str) -> str:
    if msg.guild:

        def resolve_member(id: int) -> str:
            m = msg.guild.get_member(id) or discord.utils.get(msg.mentions, id=id)  # type: ignore
            return f"@{m.display_name}" if m else "@deleted-user"

        def resolve_role(id: int) -> str:
            r = msg.guild.get_role(id) or discord.utils.get(msg.role_mentions, id=id)  # type: ignore
            return f"@{r.name}" if r else "@deleted-role"

        def resolve_channel(id: int) -> str:
            c = msg.guild._resolve_channel(id)  # type: ignore
            return f"#{c.name}" if c else "#deleted-channel"

    else:

        def resolve_member(id: int) -> str:
            m = discord.utils.get(msg.mentions, id=id)
            return f"@{m.display_name}" if m else "@deleted-user"

        def resolve_role(id: int) -> str:
            return "@deleted-role"

        def resolve_channel(id: int) -> str:
            return "#deleted-channel"

    transforms = {
        "@": resolve_member,
        "@!": resolve_member,
        "#": resolve_channel,
        "@&": resolve_role,
    }

    def repl(match: re.Match) -> str:
        type = match[1]
        id = int(match[2])
        transformed = transforms[type](id)
        return transformed

    result = re.sub(r"<(@[!&]?|#)([0-9]{15,20})>", repl, text)

    return discord.utils.escape_mentions(result)


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


def emojify_item(d, item: str, default: Any = SENTINEL) -> str | Any:
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
        return d.emojis.air if default is SENTINEL else default


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

        support_guild = bot.get_guild(bot.k.support_server_id)

        if support_guild is None:
            support_guild = await bot.fetch_guild(bot.k.support_server_id)

        role_map_values = set(bot.d.role_mappings.values())

        roles = []

        for role in member.roles:  # add non rank roles to roles list
            if role.id not in role_map_values and role.id != bot.k.support_server_id:
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


def shorten_chunks(items: list[str], max_size: int) -> Generator[str, None, None]:
    size = 0

    for item in items:
        if len(item) + size > max_size:
            break

        size += len(item)

        yield item


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


def shorten_text(text: str, to: int = 2000) -> str:
    if len(text) > to:
        return text[: to - 1] + "…"

    return text


def check_file_signature(*, media_type: str, file_name: str) -> bool:
    return mimetypes.types_map["." + file_name.split(".")[-1]] == media_type


def is_valid_image_res(res: aiohttp.ClientResponse) -> bool:
    if not res.content_type.startswith("image/"):
        return False

    return True


async def read_limited(res: aiohttp.ClientResponse, *, max_bytes: int = 1e6) -> bytes:
    out = bytearray()

    async for data in res.content.iter_any():
        out.extend(data)

        if len(out) > max_bytes:
            raise ValueError("Content length exceeds max length")

    return bytes(out)


def item_case(text: str) -> str:
    return " ".join([w.capitalize() for w in text.split()])


async def fetch_aprox_ban_count(guild: discord.Guild, seconds: float, chunk_size: int = 500) -> str:
    assert chunk_size > 0

    start_time: float = time.time()
    last_entry: discord.User | None = None
    ban_count = 0

    while True:
        # ran out of time
        if (time.time() - start_time) > seconds:
            return f"{ban_count}+"

        ban_entries_chunk = [e async for e in guild.bans(limit=chunk_size, after=last_entry)]

        if ban_entries_chunk:
            last_entry = ban_entries_chunk[-1].user
            ban_count += len(ban_entries_chunk)

        # there are no more ban entries to fetch
        if len(ban_entries_chunk) < chunk_size or last_entry is None:
            return str(ban_count)


def text_to_discord_file(text: str, *, file_name: str | None = None) -> discord.File:
    file_data = io.BytesIO(text.encode(encoding="utf8"))
    file_data.seek(0)
    return discord.File(file_data, filename=file_name)
