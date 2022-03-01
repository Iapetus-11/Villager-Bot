import asyncio
import io
import os
import sys
from contextlib import redirect_stderr, redirect_stdout
from typing import Union

import aiofiles
import arrow
import disnake
from bot import VillagerBotCluster
from disnake.ext import commands
from util.code import execute_code, format_exception
from util.ipc import PacketType
from util.misc import SuppressCtxManager


class Owner(commands.Cog):
    def __init__(self, bot: VillagerBotCluster):
        self.bot = bot

        self.ipc = bot.ipc
        self.d = bot.d
        self.db = bot.get_cog("Database")

    async def cog_before_invoke(self, ctx):
        print(f"{ctx.author}: {ctx.message.content}")

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_cog(self, ctx, cog: str):
        res = await self.ipc.broadcast({"type": PacketType.EVAL, "code": f"bot.reload_extension('cogs.{cog}')"})

        for response in res.responses:
            if not response.success:
                await ctx.send(f"Error while reloading `cogs.{cog}`: ```py\n{response.result}```")
                return

        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="reloaddata", aliases=["update", "updatedata"])
    @commands.is_owner()
    async def update_data(self, ctx):
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
    async def eval_stuff_local(self, ctx, *, stuff: str):
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
    async def eval_stuff_global(self, ctx, *, stuff: str):
        stuff = stuff.strip(" `\n")

        if stuff.startswith("py"):
            stuff = stuff[2:]

        res = await self.ipc.broadcast({"type": PacketType.EXEC, "code": stuff})

        await ctx.reply("".join([f"```py\n{str(r.result).replace('```', '｀｀｀')}```" for r in res.responses])[:2000])

    @commands.command(name="gitpull")
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=True)
    @commands.is_owner()
    async def gitpull(self, ctx):
        async with SuppressCtxManager(ctx.typing()):
            await self.bot.loop.run_in_executor(self.bot.tp, os.system, "git pull > git_pull_log 2>&1")

            async with aiofiles.open("git_pull_log", "r") as f:
                await ctx.reply(f"```diff\n{(await f.read())[:2000-11]}```")

        os.remove("git_pull_log")

    @commands.command(name="lookup")
    @commands.is_owner()
    async def lookup(self, ctx, user: Union[disnake.User, int]):
        if isinstance(user, disnake.User):
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
    async def set_user_bal(self, ctx, user: Union[disnake.User, int], balance: int):
        if isinstance(user, disnake.User):
            uid = user.id
        else:
            uid = user

        await self.db.update_user(uid, emeralds=balance)
        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="botban")
    @commands.is_owner()
    async def ban_user_from_bot(self, ctx, user: Union[disnake.User, int]):
        if isinstance(user, disnake.User):
            uid = user.id
        else:
            uid = user

        await self.db.update_user(uid, bot_banned=True)
        await self.ipc.broadcast({"type": PacketType.EVAL, "code": f"self.ban_cache.add({uid})"})

        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="unbotban")
    @commands.is_owner()
    async def unban_user_from_bot(self, ctx, user: Union[disnake.User, int]):
        if isinstance(user, disnake.User):
            uid = user.id
        else:
            uid = user

        await self.db.update_user(uid, bot_banned=False)
        await self.ipc.broadcast({"type": PacketType.EVAL, "code": f"self.ban_cache.remove({uid})"})

        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="givehistory", aliases=["transactions", "givelogs", "tradelogs"])
    @commands.is_owner()
    async def transaction_history(self, ctx, user: Union[disnake.User, int]):
        if isinstance(user, disnake.User):
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

        page_max = await self.db.fetch_transactions_page_count(uid)
        page = 0

        msg = None
        first_time = True

        while True:
            entries = await self.db.fetch_transactions_page(uid, page=page)

            if len(entries) == 0:
                embed = disnake.Embed(color=self.d.cc, description=ctx.l.econ.inv.empty)

                if user is not None:
                    embed.set_author(
                        name=f"Transaction history for {username}", icon_url=getattr(user.avatar, "url", embed.Empty)
                    )
                else:
                    embed.set_author(name=f"Transaction history for {username}")
            else:
                body = ""  # text for that page

                for entry in entries:
                    giver = self.bot.get_user(entry["sender"])
                    receiver = self.bot.get_user(entry["receiver"])
                    item = entry["item"]

                    if item == "emerald":
                        item = self.d.emojis.emerald

                    body += f"__[{giver}]({entry['sender']})__ *gave* __{entry['amount']}x **{item}**__ *to* __[{receiver}]({entry['receiver']})__ *{arrow.get(entry['at']).humanize()}*\n"

                embed = disnake.Embed(color=self.d.cc, description=body)
                embed.set_author(name=f"Transaction history for {user}", icon_url=getattr(user.avatar, "url", embed.Empty))
                embed.set_footer(text=f"Page {page+1}/{page_max+1}")

            if msg is None:
                msg = await ctx.reply(embed=embed, mention_author=False)
            else:
                await msg.edit(embed=embed)

            if page_max > 0:
                if first_time:
                    await msg.add_reaction("⬅️")
                    await asyncio.sleep(0.1)
                    await msg.add_reaction("➡️")
                    await asyncio.sleep(0.1)

                try:

                    def author_check(react, r_user):
                        return r_user == ctx.author and ctx.channel == react.message.channel and msg == react.message

                    react, r_user = await self.bot.wait_for(
                        "reaction_add", check=author_check, timeout=(3 * 60)
                    )  # wait for reaction from message author
                except asyncio.TimeoutError:
                    await asyncio.wait((msg.remove_reaction("⬅️", ctx.me), msg.remove_reaction("➡️", ctx.me)))
                    return

                await react.remove(ctx.author)

                if react.emoji == "⬅️":
                    page -= 1 if page - 1 >= 0 else 0
                if react.emoji == "➡️":
                    page += 1 if page + 1 <= page_max else 0

                await asyncio.sleep(0.1)
            else:
                break

            first_time = False


def setup(bot):
    bot.add_cog(Owner(bot))
