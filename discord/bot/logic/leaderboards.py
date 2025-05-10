import asyncio
from typing import Any

import discord


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

    return body + "\ufeff"


async def craft_lbs(
    bot,
    global_lb: list[dict[str, Any]],
    local_lb: list[dict[str, Any]],
    row_fstr: str,
) -> tuple[str, str]:
    return await asyncio.gather(
        _craft_lb(bot, global_lb, row_fstr),
        _craft_lb(bot, local_lb, row_fstr),
    )
