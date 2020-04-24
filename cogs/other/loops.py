from discord.ext import commands
import discord
import asyncio
import logging
from random import choice
import json
import dbl
import arrow


class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.g = self.bot.get_cog("Global")
        self.db = self.bot.get_cog("Database")

        self.logger = logging.getLogger("Loops")
        self.logger.setLevel(logging.INFO)

    async def update_activity(self):
        while self.bot.is_ready():
            await asyncio.sleep(3600)
            await self.bot.change_presence(activity=discord.Game(name=choice(self.g.playingList)))
            self.logger.info(" Updated Activity")

    async def reset_cmd_vect_counter(self):
        while self.bot.is_ready():
            await asyncio.sleep(1)
            self.g.cmd_vect = 0

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(self.update_activity())
        self.bot.loop.create_task(self.reset_cmd_vect_counter())


def setup(bot):
    bot.add_cog(Loops(bot))
