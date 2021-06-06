from discord.ext import commands


class Sex(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sex")
    async def sex(self, ctx):
        await ctx.send("https://knowyourmeme.com/memes/trollface")

    @commands.command(name="boobs", aliases=["tits", "bigbooba"])
    async def big_booba(self, ctx):
        await ctx.send("https://knowyourmeme.com/memes/trollface")

    @commands.command(name="pussy")
    async def pussy(self, ctx):
        await ctx.send("https://knowyourmeme.com/memes/trollface")


def setup(bot):
    bot.add_cog(Sex(bot))
