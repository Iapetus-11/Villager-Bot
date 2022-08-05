import io
import os
import sys
from contextlib import redirect_stderr, redirect_stdout
from typing import Union

import aiofiles
import arrow
import discord
from cogs.core.paginator import Paginator
from discord.ext import commands
from util.code import execute_code, format_exception
from util.ctx import Ctx
from util.ipc import PacketType
from util.misc import SuppressCtxManager

from bot import VillagerBotCluster


class Owner(commands.Cog):
    def __init__(self, bot: VillagerBotCluster):
        self.bot = bot

        self.ipc = bot.ipc
        self.d = bot.d
        self.db = bot.get_cog("Database")

    async def cog_before_invoke(self, ctx: Ctx):
        print(f"{ctx.author}: {ctx.message.content}")

    @property
    def paginator(self) -> Paginator:
        return self.bot.get_cog("Paginator")

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_cog(self, ctx: Ctx, cog: str):
        res = await self.ipc.broadcast({"type": PacketType.EVAL, "code": f"bot.reload_extension('cogs.{cog}')"})

        for response in res.responses:
            if not response.success:
                await ctx.send(f"Error while reloading `cogs.{cog}`: ```py\n{response.result}```")
                return

        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="reloaddata", aliases=["update", "updatedata"])
    @commands.is_owner()
    async def update_data(self, ctx: Ctx):
        """Reloads data from data.json and text from the translation files"""

        res = await self.ipc.broadcast({"type": PacketType.RELOAD_DATA})
        failed = False

        for data in res.responses:
            if not data.success:
                failed = True
                await ctx.reply_embed(f"Updating data failed: ```py\n{data.result}\n```")

        if not failed:
            await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="evallocal", aliases=["eval", "evall"])
    @commands.is_owner()
    async def eval_stuff_local(self, ctx: Ctx, *, stuff: str):
        stuff = stuff.strip(" `\n")

        if stuff.startswith("py"):
            stuff = stuff[2:]

        try:
            out = io.StringIO()

            with redirect_stdout(out), redirect_stderr(out):
                result = await execute_code(stuff, {**globals(), **locals(), **self.bot.eval_env})

            sys.stdout.write(out.getvalue())

            result_str = f"{out.getvalue()}{result}".replace("```", "｀｀｀")
            await ctx.reply(f"```\n{result_str}```")
        except Exception as e:
            print("Exception:", e)
            await ctx.reply(f"```py\n{format_exception(e)[:2000-9].replace('```', '｀｀｀')}```")

    @commands.command(name="evalglobal", aliases=["evalall", "evalg"])
    @commands.is_owner()
    async def eval_stuff_global(self, ctx: Ctx, *, stuff: str):
        stuff = stuff.strip(" `\n")

        if stuff.startswith("py"):
            stuff = stuff[2:]

        res = await self.ipc.broadcast({"type": PacketType.EXEC, "code": stuff})

        contents = [f"```py\n\uFEFF{str(r.result).replace('```', '｀｀｀')}"[:1997] + "```" for r in res.responses]
        joined = "".join(contents)

        if len(joined) > 2000:
            for content in contents:
                await ctx.reply(content)
        else:
            await ctx.reply("".join(joined))

    @commands.command(name="gitpull")
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=True)
    @commands.is_owner()
    async def gitpull(self, ctx: Ctx):
        async with SuppressCtxManager(ctx.typing()):
            await self.bot.loop.run_in_executor(self.bot.tp, os.system, "git pull > git_pull_log 2>&1")

            async with aiofiles.open("git_pull_log", "r") as f:
                await ctx.reply(f"```diff\n{(await f.read())[:2000-11]}```")

        os.remove("git_pull_log")

    @commands.command(name="lookup")
    @commands.is_owner()
    async def lookup(self, ctx: Ctx, user: Union[discord.User, int]):
        if isinstance(user, discord.User):
            uid = user.id
        else:
            uid = user

        format_str = '"{guild} **|** `{guild.id}`\\n"'  # vsc can't handle nested formatting cause stupid
        code = f"""
        guilds = ""
        for guild in bot.guilds:
            if guild.get_member({uid}) is not None:
                guilds += f{format_str}
        return guilds
        """

        res = await self.ipc.broadcast({"type": PacketType.EXEC, "code": code})

        guilds = "".join([r.result for r in res.responses])

        if guilds == "":
            await ctx.reply_embed("No results...")
        else:
            await ctx.reply_embed(guilds)

    @commands.command(name="setbal")
    @commands.is_owner()
    async def set_user_bal(self, ctx: Ctx, user: Union[discord.User, int], balance: int):
        if isinstance(user, discord.User):
            uid = user.id
        else:
            uid = user

        await self.db.update_user(uid, emeralds=balance)
        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="botban")
    @commands.is_owner()
    async def ban_user_from_bot(self, ctx: Ctx, user: Union[discord.User, int]):
        if isinstance(user, discord.User):
            uid = user.id
        else:
            uid = user

        await self.db.update_user(uid, bot_banned=True)
        await self.ipc.broadcast({"type": PacketType.EVAL, "code": f"self.ban_cache.add({uid})"})

        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="unbotban")
    @commands.is_owner()
    async def unban_user_from_bot(self, ctx: Ctx, user: Union[discord.User, int]):
        if isinstance(user, discord.User):
            uid = user.id
        else:
            uid = user

        await self.db.update_user(uid, bot_banned=False)
        await self.ipc.broadcast({"type": PacketType.EVAL, "code": f"self.ban_cache.remove({uid})"})

        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="givehistory", aliases=["transactions", "givelogs", "tradelogs"])
    @commands.is_owner()
    async def transaction_history(self, ctx: Ctx, user: Union[discord.User, int]):
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

            embed = discord.Embed(color=self.d.cc, description=ctx.l.econ.inv.empty)

            if len(entries) == 0:
                embed.set_author(
                    name=f"Transaction history for {username}",
                    icon_url=(getattr(user.avatar, "url", embed.Empty) if user else embed.Empty),
                )

                return embed

            body = ""

            for entry in entries:
                giver = getattr(ctx.guild.get_member(entry["sender"]), "mention", None) or f"`{entry['sender']}`"
                receiver = getattr(ctx.guild.get_member(entry["receiver"]), "mention", None) or f"`{entry['receiver']}`"
                item = entry["item"]

                if item == "emerald":
                    item = self.d.emojis.emerald

                body += f"__[{giver}]({entry['sender']})__ *gave* __{entry['amount']}x **{item}**__ *to* __[{receiver}]({entry['receiver']})__ *{arrow.get(entry['at']).humanize()}*\n"

            embed = discord.Embed(color=self.d.cc, description=body)
            embed.set_author(name=f"Transaction history for {user}", icon_url=getattr(user.avatar, "url", embed.Empty))
            embed.set_footer(text=f"Page {page+1}/{page_count}")

            return embed

        await self.paginator.paginate_embed(ctx, get_page, timeout=60, page_count=page_count)

    @commands.command(name="jlstats", aliases=["joinleavestats", "joinsleaves", "jls"])
    @commands.is_owner()
    async def joinleaves(self, ctx: Ctx):
        async with SuppressCtxManager(ctx.typing()):
            records = await self.db.db.fetch(
                """SELECT COALESCE(join_count, 0) AS join_count, COALESCE(leave_count, 0) AS leave_count, COALESCE(iq1.event_at_trunc, iq2.event_at_trunc) AS event_at FROM (
            SELECT COUNT(*) AS join_count, DATE_TRUNC('day', event_at) AS event_at_trunc FROM guild_events WHERE event_type = 1 GROUP BY event_at_trunc ORDER BY event_at_trunc ASC
        ) iq1
        FULL OUTER JOIN (
            SELECT COUNT(*) AS leave_count, DATE_TRUNC('day', event_at) AS event_at_trunc FROM guild_events WHERE event_type = 2 GROUP BY event_at_trunc ORDER BY event_at_trunc ASC
    ) iq2 ON iq1.event_at_trunc = iq2.event_at_trunc ORDER BY iq1.event_at_trunc DESC LIMIT 14;"""
            )

        rows = [record["join_count"] - record["leave_count"] for record in records]
        rows = [("+" if r > 0 else "-") + "#" * abs(r) + f" ({r:+})" for r in rows]

        body = "\n".join(rows)

        await ctx.send(f"Last 14 days of guild joins / leaves (newest is top)```diff\n{body}\n```")


def setup(bot):
    bot.add_cog(Owner(bot))
