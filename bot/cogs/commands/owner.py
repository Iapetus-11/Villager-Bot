import datetime
import math
import typing
from typing import Any

import arrow
import discord
from discord.ext import commands

from common.utils.code import execute_code, format_exception

from bot.cogs.core.database import Database
from bot.cogs.core.paginator import Paginator
from bot.utils.ctx import Ctx
from bot.utils.misc import SuppressCtxManager, parse_timedelta, shorten_text
from bot.villager_bot import VillagerBotCluster


class Owner(commands.Cog):
    def __init__(self, bot: VillagerBotCluster):
        self.bot = bot

        self.karen = bot.karen
        self.d = bot.d

    async def cog_before_invoke(self, ctx: Ctx):
        self.bot.logger.info(
            "User %s (%s) executed command %s", ctx.author.id, ctx.author, ctx.message.content
        )

    @property
    def db(self) -> Database:
        return typing.cast(self.bot.get_cog("Database"), Database)

    @property
    def paginator(self) -> Paginator:
        return typing.cast(self.bot.get_cog("Paginator"), Paginator)

    @commands.command(name="ownercommands", aliases=["ocmds", "ownerhelp", "ohelp", "ownercmds"])
    @commands.is_owner()
    async def owner_commands(self, ctx: Ctx):
        await ctx.reply_embed(f"`{'`, `'.join(map(str, self.get_commands()))}`")

    @commands.command(name="evallocal", aliases=["eval", "evall"])
    @commands.is_owner()
    async def eval_stuff_local(self, ctx: Ctx, *, stuff: str):
        stuff = stuff.strip(" `\n")

        if stuff.startswith("py"):
            stuff = stuff[2:]

        try:
            result = await execute_code(
                stuff,
                {
                    "bot": self.bot,
                    "db": self.db.db,
                    "dbc": self.db,
                    "http": self.bot.aiohttp,
                    "ctx": ctx,
                },
            )

            result_str = f"{result}".replace("```", "｀｀｀")
            await ctx.reply(f"```\n{result_str}```")
        except Exception as e:
            await ctx.reply(f"```py\n{format_exception(e)[:2000-9].replace('```', '｀｀｀')}```")

    @commands.command(name="evalglobal", aliases=["evalall", "evalg"])
    @commands.is_owner()
    async def eval_stuff_global(self, ctx: Ctx, *, stuff: str):
        stuff = stuff.strip(" `\n")

        if stuff.startswith("py"):
            stuff = stuff[2:]

        responses = await self.karen.exec_code_all(stuff)

        contents = [
            f"```py\n\uFEFF{str(r).replace('```', '｀｀｀')}"[:1997] + "```" for r in responses
        ]
        joined = "".join(contents)

        if len(joined) > 2000:
            for content in contents:
                await ctx.reply(content)
        else:
            await ctx.reply("".join(joined))

    @commands.command(name="lookup")
    @commands.is_owner()
    async def lookup(self, ctx: Ctx, user: discord.User | int):
        if not (uid := getattr(user, "id", None)):
            uid = user

        if uid == self.bot.user.id:
            await ctx.reply_embed("You do not want to do this.")
            return

        member_matches = await self.karen.lookup_user(uid)

        if not member_matches:
            await ctx.reply_embed("No results...")
        else:
            await ctx.reply_embed("\n".join([f"`{mm[0]}` **|** {mm[1]}" for mm in member_matches]))

    @commands.command(name="setbal")
    @commands.is_owner()
    async def set_user_bal(self, ctx: Ctx, user: discord.User | int, balance: int):
        if not (uid := getattr(user, "id", None)):
            uid = user

        await self.db.update_user(uid, emeralds=balance)
        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="botban")
    @commands.is_owner()
    async def ban_user_from_bot(self, ctx: Ctx, user: discord.User | int):
        if isinstance(user, discord.User):
            uid = user.id
        else:
            uid = user

        await self.db.update_user(uid, bot_banned=True)
        await self.karen.botban_cache_add(uid)

        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="unbotban")
    @commands.is_owner()
    async def unban_user_from_bot(self, ctx: Ctx, user: discord.User | int):
        if isinstance(user, discord.User):
            uid = user.id
        else:
            uid = user

        await self.db.update_user(uid, bot_banned=False)
        await self.karen.botban_cache_remove(uid)

        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="givehistory", aliases=["transactions", "givelogs", "tradelogs"])
    @commands.is_owner()
    async def transaction_history(self, ctx: Ctx, user: discord.User | int):
        if isinstance(user, discord.User):
            uid = user.id
            username = str(user)
        else:
            uid = user
            user = None

            try:
                user = await self.bot.fetch_user(uid)
                username = str(user)
            except Exception:
                username = "Unknown User"

        page_count = await self.db.fetch_transactions_page_count(uid)

        async def get_page(page: int) -> discord.Embed:
            entries = await self.db.fetch_transactions_page(uid, page=page)

            embed = discord.Embed(color=self.bot.embed_color, description=ctx.l.econ.inv.empty)

            embed.set_author(
                name=f"Transaction history for {username}",
                icon_url=(getattr(user.avatar, "url", None) if user else None),
            )

            if len(entries) == 0:
                return embed

            body = ""

            for entry in entries:
                giver = f"<@{entry['sender']}>"
                receiver = f"<@{entry['receiver']}>"
                item = entry["item"]

                if item == "emerald":
                    item = self.d.emojis.emerald

                body += f"__{giver} ({entry['sender']})__ *gave* __{entry['amount']}x **{item}**__ *to* __{receiver} ({entry['receiver']})__ *{arrow.get(entry['at']).humanize()}*\n"

            embed = discord.Embed(color=self.bot.embed_color, description=body)
            embed.set_author(
                name=f"Transaction history for {user}",
                icon_url=getattr(user.avatar, "url", None),
            )
            embed.set_footer(text=f"Page {page+1}/{page_count}")

            return embed

        await self.paginator.paginate_embed(ctx, get_page, timeout=60, page_count=page_count)

    @commands.command(name="jlstats", aliases=["joinleavestats", "joinsleaves", "jls"])
    @commands.is_owner()
    async def joinleaves(self, ctx: Ctx):
        async with SuppressCtxManager(ctx.typing()):
            rows = await self.db.fetch_guilds_jls()

            rows = [row["diff"] for row in rows]
            rows = [
                ("+" if r > 0 else "-" if r < 0 else "~")
                + " "
                + (("#" * abs(r)) if r < 30 else ("#" * 30 + "+"))
                + (f" ({r:+})" if r != 0 else "")
                for r in rows
            ]

            body = "\n".join(rows)

        await ctx.send(f"Last 14 days of guild joins / leaves (newest is top)```diff\n{body}\n```")

    @commands.command(name="topguilds", aliases=["topgs"])
    @commands.is_owner()
    async def top_guilds(self, ctx: Ctx):
        def format_lb(values: list[dict[str, Any]]) -> str:
            return (
                "```md\n##  count  | guild id            | name\n"
                + "\n".join(
                    [
                        f"{f'{i+1}.':<3} {g['count']:<6} | {g['id']:<19} | "
                        f"{shorten_text(g['name'].replace('_', '').replace('*', '').replace('`', ''), 40)}"
                        for i, g in enumerate(values)
                    ]
                )
                + "```"
            )

        async with SuppressCtxManager(ctx.typing()):
            top_guilds_by_members = format_lb(
                sorted(
                    await self.karen.fetch_top_guilds_by_members(),
                    key=(lambda g: g["count"]),
                    reverse=True,
                )[:10]
            )
            top_guilds_by_active_members = format_lb(
                sorted(
                    await self.karen.fetch_top_guilds_by_active_members(),
                    key=(lambda g: g["count"]),
                    reverse=True,
                )[:10]
            )
            top_guilds_by_commands = format_lb(
                sorted(
                    await self.karen.fetch_top_guilds_by_commands(),
                    key=(lambda g: g["count"]),
                    reverse=True,
                )[:10]
            )

        await ctx.reply(
            f"**By Members**\n{top_guilds_by_members}\n\n"
            f"**By Active Members** (those who executed a command within last 7 days)\n{top_guilds_by_active_members}\n\n"
            f"**By Commands** (last 30 days)\n{top_guilds_by_commands}\n\n"
        )

    @commands.command(name="commandstreaks", aliases=["cmdsstreaks", "cmdstreaks"])
    @commands.is_owner()
    async def command_streaks(self, ctx: Ctx, duration_str: str = "5m"):
        duration = parse_timedelta(duration_str)

        if duration is None or duration.total_seconds() <= 0:
            await ctx.reply_embed("Invalid duration specified")
            return

        def format_row(idx_row) -> str:
            idx: int
            row: dict[str, Any]
            idx, row = idx_row

            td_trunc = row["duration"] - datetime.timedelta(
                days=row["duration"].days, microseconds=row["duration"].microseconds
            )

            return (
                f"{f'{idx + 1}.':<2} {td_trunc.days:02} {str(td_trunc).split(',')[-1]:0>8} | {row['user_id']:<19} "
                f"| {str(self.bot.get_user(row['user_id']) or '').replace('_', '').replace('*', '').replace('`', '')}"
            )

        async with SuppressCtxManager(ctx.typing()):
            command_streaks = await self.db.fetch_command_streaks(
                break_interval=duration,
                after=arrow.utcnow().shift(days=-7).datetime,
                limit=9,
            )

            formatted_rows = "\n".join(map(format_row, enumerate(command_streaks)))

        await ctx.reply(
            f"**Command Streaks** (last week)\n```md\n## d  h  m  s  | user id             | name\n{formatted_rows}\n```"
        )

    @commands.command(name="commandstats", aliases=["cmdstats"])
    @commands.is_owner()
    async def command_stats(self, ctx: Ctx, interval: str = "7d"):
        async with SuppressCtxManager(ctx.typing()):
            delta = parse_timedelta(interval)

            command_stats = await self.db.get_command_uses_per_day_over(delta)

            rows = [(r["count"], int(math.log(r["count"] + 1, 10) * 5)) for r in command_stats]
            rows = [("#" * s) + (f" ({v})" if s != 0 else "") for (v, s) in rows]
            rows = "\n".join(rows)

            await ctx.reply(
                f"Last {math.ceil(delta.total_seconds() / 3600 / 24)} days of commands per day:\n```c\n{rows}\n```"
            )

    @commands.command(
        name="transfer_inventory", aliases=["invtransfer", "auction", "transferinv", "trinv"]
    )
    @commands.is_owner()
    async def transfer_inventory(
        self, ctx: Ctx, from_user: int | discord.User, to_user: int | discord.User
    ):
        if isinstance(from_user, int):
            from_user = self.bot.get_user(from_user) or await self.bot.fetch_user(from_user)

        if isinstance(to_user, int):
            to_user = self.bot.get_user(to_user) or await self.bot.fetch_user(to_user)

        item_count = 0
        for item in await self.db.fetch_items(from_user.id):
            if item.sticky or not item.sellable:
                continue

            item_count += 1
            await self.db.remove_item(from_user.id, item.name, item.amount)
            await self.db.add_item(
                to_user.id, item.name, item.sell_price, item.amount, item.sticky, item.sellable
            )

        await ctx.reply(
            f"{self.d.emojis.yes} Transferred **{item_count}** items from {from_user.mention} to {to_user.mention}."
        )

    @commands.command(name="shutdown")
    @commands.is_owner()
    async def shutdown(self, ctx: Ctx):
        await ctx.message.add_reaction(self.d.emojis.yes)
        await self.karen.shutdown()

    @commands.command(name="interror")
    @commands.is_owner()
    async def intentional_error(self, ctx: Ctx):
        raise Exception("intentional!")

    @commands.command(name="intwarning", aliases=["intwarn"])
    @commands.is_owner()
    async def intentional_warning(self, ctx: Ctx):
        self.bot.logger.warning("intentional warning !!!!!!!!")


async def setup(bot: VillagerBotCluster) -> None:
    await bot.add_cog(Owner(bot))
