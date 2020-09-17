from discord.ext import commands
import discord


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = self.bot.d

    @commands.command(name='load')
    @commands.is_owner()
    async def load_cog(self, ctx, cog):
        self.bot.load_extension(f'cogs.{cog}')

    @commands.command(name='unload')
    @commands.is_owner()
    async def unload_cog(self, ctx, cog):
        self.bot.unload_extension(f'cogs.{cog}')

    @commands.command(name='reload')
    @commands.is_owner()
    async def reload_cog(self, ctx, cog):
        self.bot.reload_extension(f'cogs.{cog}')

def setup(bot):
