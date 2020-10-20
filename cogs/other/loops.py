import arrow
import asyncio
import dbl
import discord
import json
import logging
from discord.ext import commands
from os import system
from random import choice


class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.g = self.bot.get_cog("Global")
        self.db = self.bot.get_cog("Database")

        self.logger = logging.getLogger("Loops")
        self.logger.setLevel(logging.INFO)

    async def update_activity(self):
        while self.bot.is_ready():
            await asyncio.sleep(7200)
            await self.bot.change_presence(activity=discord.Game(name=choice(self.g.playingList)))

    async def backup_database(self):
        while self.bot.is_ready():
            await asyncio.sleep(43200)
            system("pg_dump villagerbot | gzip > ../database-backups/{0}.gz".format(
                arrow.utcnow().ctime().replace(" ", "_").replace(":", ".")))

    async def update_roles(self):
        while self.bot.is_ready():
            await asyncio.sleep(5 * 60)
            econ = self.bot.get_cog("Econ")
            for user in self.bot.get_guild(641117791272960031).members:
                await econ.update_user_role(user.id)

    async def reset_pillage_limit(self):
        while self.bot.is_ready():
            await asyncio.sleep(24 * 3600)
            self.bot.get_cog("Econ").pillage_limit = {}

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(60)
        self.bot.loop.create_task(self.update_activity())
        self.bot.loop.create_task(self.backup_database())
        self.bot.loop.create_task(self.update_roles())
        self.bot.loop.create_task(self.reset_pillage_limit())


def setup(bot):
    bot.add_cog(Loops(bot))
