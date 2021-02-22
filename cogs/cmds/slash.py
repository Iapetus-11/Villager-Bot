from discord_slash import cog_ext
from discord.ext import commands
import discord


class Slash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.d = bot.d

        self.useful = bot.get_cog("Useful")
        self.fun = bot.get_cog("Fun")

    async def prep(self, ctx):
        ctx.l = await self.bot.get_lang(ctx)

        if ctx.author.id in self.d.ban_cache:
            ctx.custom_err = "bot_banned"
            raise Exception("User is botbanned from slash commands")

        ctx.prefix = await self.bot.get_prefix(ctx)
        ctx.invoked_subcommand = None
        ctx.typing = ctx.channel.typing

        await ctx.respond()

    # @cog_ext.cog_slash(name="help", description="View helpful information about Villager Bot!")
    # async def help(self, ctx):
    #     await self.prep(ctx)
    #     await self.useful.help(ctx)
    #
    # @cog_ext.cog_subcommand(base="help", name="econ", description="View helpful information about Villager Bot's economy commands!")
    # async def help_economy(self, ctx):
    #     await self.prep(ctx)
    #     await self.useful.help_economy(ctx)
    #
    # @cog_ext.cog_subcommand(base="help", name="mc", description="View helpful information about Villager Bot's minecraft-related commands!")
    # async def help_minecraft(self, ctx):
    #     await self.prep(ctx)
    #     await self.useful.help_minecraft(ctx)
    #
    # @cog_ext.cog_subcommand(base="help", name="util", description="View helpful information about Villager Bot's utility commands!")
    # async def help_utility(self, ctx):
    #     await self.prep(ctx)
    #     await self.useful.help_utility(ctx)
    #
    # @cog_ext.cog_subcommand(base="help", name="fun", description="View helpful information about Villager Bot's fun & memey commands!")
    # async def help_fun(self, ctx):
    #     await self.prep(ctx)
    #     await self.useful.help_fun(ctx)
    #
    # @cog_ext.cog_subcommand(base="help", name="admin", description="View helpful information about Villager Bot's moderation commands!")
    # async def help_administrative(self, ctx):
    #     await self.prep(ctx)
    #     await self.useful.help_administrative(ctx)

    @cog_ext.cog_slash(name="vote", description="Earn emeralds from voting for Villager Bot on certain websites!")
    async def votelinks(self, ctx):
        await self.prep(ctx)
        await self.useful.votelinks(ctx)

    @cog_ext.cog_slash(name="invite", description="View the invite link, and some other useful links too!")
    async def useful_links(self, ctx):
        await self.prep(ctx)
        await self.useful.useful_links(ctx)

    @cog_ext.cog_slash(name="google", description="Search on Google from Discord!")
    async def google(self, ctx, query: str):
        await self.prep(ctx)
        await self.useful.google_search(ctx, query)

    @cog_ext.cog_slash(name="youtube", description="Search on Youtube from Discord!")
    async def google(self, ctx, query: str):
        await self.prep(ctx)
        await self.useful.youtube_search(ctx, query)

    @cog_ext.cog_slash(name="image", description="Search on Google images from Discord!")
    async def google(self, ctx, query: str):
        await self.prep(ctx)
        await self.useful.image_search(ctx, query)

    @cog_ext.cog_slash(name="meme", description="Sends a random meme from Reddit!")
    async def meme(self, ctx):
        await self.prep(ctx)
        await self.fun.meme(ctx)


def setup(bot):
    bot.add_cog(Slash(bot))
