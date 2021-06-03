from discord.ext import commands
from typing import Union
import functools
import aiofiles
import discord
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


def setup(bot):
    bot.add_cog(Owner(bot))
