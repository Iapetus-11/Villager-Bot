from discord.ext import commands, tasks
from classyjson import ClassyDict
import asyncio


class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Loops(bot))
