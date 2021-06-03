from discord.ext import commands
from typing import Union
import functools
import aiofiles
import asyncio
import discord
import arrow
import os

from util.code import execute_code, format_exception


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.ipc = bot.ipc
        self.d = bot.d

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_cog(self, ctx, cog: str):
        res = await self.ipc.broadcast({"type": "eval", "code": f"bot.reload_extension('cogs.{cog}')"})

        for response in res.responses:
            if not response.success:
                await ctx.send(f"Error while reloading `cogs.{cog}`: ```py\n{response.result}```")
                return

        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="evallocal", aliases=["eval", "evall"])
    @commands.is_owner()
    async def eval_stuff_local(self, ctx, *, stuff: str):
        if stuff.startswith("```"):
            stuff = stuff.lstrip(" `py\n ").rstrip(" `\n ")

        try:
            result = await execute_code(stuff, {**globals(), **locals(), **self.bot.eval_env})
            await ctx.reply(f"```{repr(result).replace('```', '｀｀｀')}```")
        except Exception as e:
            await ctx.reply(f"```py\n{format_exception(e)[:2000-9]}```")

    @commands.command(name="evalglobal", aliases=["evalall", "evalg"])
    @commands.is_owner()
    async def eval_stuff_global(self, ctx, *, stuff: str):
        if stuff.startswith("```"):
            stuff = stuff.lstrip(" `py\n ").rstrip(" `\n ")

        res = await self.ipc.broadcast({"type": "exec", "code": stuff})

        await ctx.reply("".join([f"```py\n{repr(r['result']).replace('```', '｀｀｀')}```" for r in res["responses"]])[:2000])

    @commands.command(name="gitpull")
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=True)
    @commands.is_owner()
    async def gitpull(self, ctx):
        async with ctx.typing():
            system_call = functools.partial(os.system, "git pull > git_pull_log 2>&1")
            await self.bot.loop.run_in_executor(self.bot.tp, system_call)

            async with aiofiles.open("git_pull_log", "r") as f:
                await ctx.reply(f"```diff\n{(await f.read())[:2000-11]}```")

        os.remove("git_pull_log")

    @commands.command(name="lookup")
    @commands.is_owner()
    async def lookup(self, ctx, user: Union[discord.User, int]):
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

        res = await self.ipc.broadcast({"type": "exec", "code": code})

        guilds = "".join([r.result for r in res.responses])

        if guilds == "":
            await self.bot.reply_embed(ctx, "No results...")
        else:
            await self.bot.reply_embed(ctx, guilds)

    @commands.command(name="givehistory", aliases=["transactions"])
    @commands.is_owner()
    async def transaction_history(self, ctx, user: discord.User):
        page_max = await self.db.fetch_transactions_page_count(user.id)
        page = 0

        msg = None
        first_time = True

        while True:
            entries = await self.db.fetch_transactions_page(user.id, page=page)

            if len(entries) == 0:
                body = ctx.l.econ.inv.empty
            else:
                body = ""  # text for that page

                for entry in entries:
                    giver = self.bot.get_user(entry["giver_uid"])
                    receiver = self.bot.get_user(entry["recvr_uid"])
                    item = entry["item"]

                    if item == "emerald":
                        item = self.d.emojis.emerald

                    body += f"__[{giver}]({entry['giver_uid']})__ *gave* __{entry['amount']}x **{item}**__ *to* __[{receiver}]({entry['recvr_uid']})__ *{arrow.get(entry['ts']).humanize()}*\n"

                embed = discord.Embed(color=self.d.cc, description=body)
                embed.set_author(name=f"Transaction history for {user}", icon_url=user.avatar_url_as())
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
                        return r_user == ctx.author and ctx.channel == react.message.channel and msg.id == react.message.id

                    react, r_user = await self.bot.wait_for(
                        "reaction_add", check=author_check, timeout=(3 * 60)
                    )  # wait for reaction from message author
                except asyncio.TimeoutError:
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
