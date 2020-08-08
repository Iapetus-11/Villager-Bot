from discord.ext import commands
import discord
import asyncio


class Econ(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.db = self.bot.get_cog("Database")

def setup(bot):
    bot.add_cog(Econ(bot))
