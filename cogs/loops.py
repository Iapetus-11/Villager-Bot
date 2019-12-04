from discord.ext import commands, tasks
import discord
import asyncio
import json
import dbl
from random import choice

class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(hours=3)
    async def update_activity(self):
        with open("playing.txt", "r") as file:
            playing = file.readlines()
        await self.bot.change_presence(activity=discord.Game(name=choice(playing)))

def setup(bot):
    bot.add_cog(Loops(bot))
