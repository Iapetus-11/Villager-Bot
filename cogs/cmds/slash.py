from discord_slash import cog_ext


class Slash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.d = bot.d

        self.useful = bot.get_cog("Useful")

        self.guild_ids = [641117791272960031]

    async def prep(self, ctx):
        ctx.l = await self.bot.get_lang(ctx)
        await ctx.respond()

    @commands.group(name="help")
    async def help(self, ctx):
        await self.prep(ctx)
        await self.useful.help(ctx)

    @help.command(name="economy", aliases=["econ"])
    async def help_economy(self, ctx):
        await self.prep(ctx)
        await self.useful.help_economy(ctx)

    @help.command(name="minecraft", aliases=["mc"])
    async def help_minecraft(self, ctx):
        await self.prep(ctx)
        await self.useful.help_minecraft(ctx)

    @help.command(name="utility", aliases=["util", "useful"])
    async def help_utility(self, ctx):
        await self.prep(ctx)
        await self.useful.help_utility(ctx)

    @help.command(name="fun")
    async def help_fun(self, ctx):
        await self.prep(ctx)
        await self.useful.help_fun(ctx)

    @help.command(name="administrator", aliases=["mod", "moderation", "administrative", "admin"])
    async def help_administrative(self, ctx):
        await self.prep(ctx)
        await self.useful.help_administrative(ctx)


def setup(bot):
    bot.add_cog(Slash(bot))
