from discord.ext import commands

from util.code import execute_code


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_cog(self, ctx, cog: str):
        await self.bot.ipc.send({"type": "broadcast-eval", "code": f"bot.reload_extension('cogs.{cog}')"})
        self.bot.reload_extension(f"cogs.{cog}")

    @commands.command(name="eval")
    @commands.is_owner()
    async def eval_stuff(self, ctx, *, stuff: str):
        if stuff.startswith("```"):
            stuff = stuff.lstrip(" `py\n ").rstrip(" `\n ")

        result = await execute_code(stuff, {**globals(), **locals()})
        await ctx.send(f"```{result}```")


def setup(bot):
    bot.add_cog(Owner(bot))
