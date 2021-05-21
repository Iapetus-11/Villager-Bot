from discord.ext import commands

from util.code import execute_code


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.ipc = bot.ipc
        self.d = bot.d

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_cog(self, ctx, cog: str):
        await self.ipc.broadcast({"type": "eval", "code": f"bot.reload_extension('cogs.{cog}')"})
        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="evallocal", aliases=["evall"])
    @commands.is_owner()
    async def eval_stuff_local(self, ctx, *, stuff: str):
        if stuff.startswith("```"):
            stuff = stuff.lstrip(" `py\n ").rstrip(" `\n ")

        result = await execute_code(stuff, {**globals(), **locals(), **self.bot.eval_env})
        await ctx.send(f"```{result}```")

    @commands.command(name="evalglobal", aliases=["evalall", "evalg"])
    @commands.is_owner()
    async def eval_stuff_global(self, ctx, *, stuff: str):
        if stuff.startswith("```"):
            stuff = stuff.lstrip(" `py\n ").rstrip(" `\n ")

        res = await self.ipc.broadcast({"type": "exec", "code": stuff})

        await ctx.send("".join([f"```py\n{r['result']}```" for r in res["responses"]]))

    @commands.command(name="test")
    @commands.is_owner()
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def test_cooldowns(self, ctx):
        await ctx.send("test")


def setup(bot):
    bot.add_cog(Owner(bot))
