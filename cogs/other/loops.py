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

        with open("data/keys.json", "r") as k:
            keys = json.load(k)

        self.dblpy = dbl.DBLClient(self.bot, keys["dblpy"])

        self.logger = logging.getLogger("Loops")
        self.logger.setLevel(logging.INFO)

        self.did_setup = False

    async def update_topgg_stats(self):
        while True:
            await self.dblpy.post_guild_count()
            self.logger.info(" Updated Top.gg Stats")
            await asyncio.sleep(1800)

    async def update_activity(self):
        while True:
            await asyncio.sleep(3600)
            await self.bot.change_presence(activity=discord.Game(name=choice(self.g.playingList)))
            self.logger.info(" Updated Activity")

    async def reset_counters(self):
        while True:
            await asyncio.sleep(1)
            self.g.cmd_vect = 0

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.did_setup:
            self.bot.loop.create_task(self.update_activity())
            self.bot.loop.create_task(self.update_topgg_stats())
            self.bot.loop.create_task(self.reset_counters())
            self.did_setup = True


def setup(bot):
    bot.add_cog(Loops(bot))
