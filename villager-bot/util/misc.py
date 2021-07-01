import classyjson as cj
import asyncpg
import discord
import math


def strip_command(ctx):  # returns message.clean_content excluding the command used
    length = len(ctx.prefix) + len(ctx.invoked_with) + 1
    return ctx.message.clean_content[length:]


def dm_check(ctx):
    def _dm_check(m):
        return ctx.author.id == m.author.id and ctx.author.dm_channel.id == m.channel.id

    return _dm_check


def recursive_update(obj, new):
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


def make_health_bar(health: int, max_health: int, full: str, half: str, empty: str):
    assert max_health % 2 == 0

    return (
        (full * (health // 2))
        + (half * (health % 2))
        + (empty * ((max_health // 2) - math.ceil(health / 2)))
        + f" ({health}/{max_health})"
    )


def lb_logic(self: object, lb_list: list, u_entry: object, rank_fstr: str):
    # add user entry to leaderboard if it's not there already
    if u_entry is not None and u_entry[0] not in [e[0] for e in lb_list]:
        lb_list.append(u_entry)

    # sort
    lb_list = sorted(lb_list, key=(lambda e: e[1]), reverse=True)

    # shorten list
    lb_list = lb_list[:9] if (u_entry is not None and u_entry[2] > 9) else lb_list[:10]

    body = ""

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


def calc_total_wealth(db_user, u_items):
    return (
        db_user["emeralds"]
        + db_user.get("vault_bal", 0) * 9
        + sum([u_it["sell_price"] * u_it.get("amount", 0) for u_it in u_items if u_it["sell_price"] > 0])
    )


def emojify_item(d, item: str):
    try:
        emoji_key = d.emoji_items[item]

        if emoji_key.startswith("fish."):
            return d.emojis.fish[emoji_key[5:]]

        return d.emojis[emoji_key]
    except KeyError:
        return d.emojis.air


def format_required(d: object, shop_item: object, amount: int = 1):
    base = f" {shop_item.buy_price * amount}{d.emojis.emerald}"

    for req_item, req_amount in shop_item.requires.get("items", {}).items():
        base += f" + {req_amount * amount}{d.emojis[d.emoji_items[req_item]]}"

    return base


def emojify_badges(badge_emojis: dict, user_badges: asyncpg.Record) -> str:
    final = []

    for badge, value in dict(user_badges).items():
        if not value:
            continue

        emoji_entry = badge_emojis[badge]

        if isinstance(emoji_entry, list):
            final.append(emoji_entry[value - 1])
        else:
            final.append(emoji_entry)
