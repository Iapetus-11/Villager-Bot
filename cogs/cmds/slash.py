from discord_slash import cog_ext
from discord.ext import commands
import discord


class Slash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.d = bot.d

        self.useful = bot.get_cog("Useful")

    async def prep(self, ctx):
        ctx.l = await self.bot.get_lang(ctx)
        await ctx.respond()

    @cog_ext.cog_slash(name="help", description="View helpful information about Villager Bot!", guild_ids=[641117791272960031])
    async def help(self, ctx):
        await self.prep(ctx)
        await self.useful.help(ctx)

    @cog_ext.cog_subcommand(base="help", name="econ", description="View helpful information about Villager Bot's economy commands!", guild_ids=[641117791272960031])
    async def help_economy(self, ctx):
        await self.prep(ctx)
        await self.useful.help_economy(ctx)

    @cog_ext.cog_subcommand(base="help", name="mc", description="View helpful information about Villager Bot's minecraft-related commands!", guild_ids=[641117791272960031])
    async def help_minecraft(self, ctx):
        await self.prep(ctx)
        await self.useful.help_minecraft(ctx)

    @cog_ext.cog_subcommand(base="help", name="util", description="View helpful information about Villager Bot's utility commands!", guild_ids=[641117791272960031])
    async def help_utility(self, ctx):
        await self.prep(ctx)
        await self.useful.help_utility(ctx)

    @cog_ext.cog_subcommand(base="help", name="fun", description="View helpful information about Villager Bot's fun & memey commands!", guild_ids=[641117791272960031])
    async def help_fun(self, ctx):
        await self.prep(ctx)
        await self.useful.help_fun(ctx)

    @cog_ext.cog_subcommand(base="help", name="admin", description="View helpful information about Villager Bot's moderation commands!", guild_ids=[641117791272960031])
    async def help_administrative(self, ctx):
        await self.prep(ctx)
        await self.useful.help_administrative(ctx)


def setup(bot):
    bot.add_cog(Slash(bot))
