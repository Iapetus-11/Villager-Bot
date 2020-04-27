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

    async def reset_cmd_vect_counter(self):
        while self.bot.is_ready():
            await asyncio.sleep(1)
            self.g.cmd_vect[1] = self.g.cmd_vect[0]
            self.g.cmd_vect[0] = 0

    async def reset_vote_vect_counter(self):
        while self.bot.is_ready():
            await asyncio.sleep(3600)
            self.g.vote_vect[1] = self.g.vote_vect[0]
            self.g.vote_vect[0] = 0

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(self.update_activity())
        self.bot.loop.create_task(self.reset_cmd_vect_counter())
        self.bot.loop.create_task(self.reset_vote_vect_counter())


def setup(bot):
    bot.add_cog(Loops(bot))
