from discord.ext import commands
import discord
import asyncio
import logging
from random import choice
import json
import dbl

class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.g = self.bot.get_cog("Global")
        
        with open("data/keys.json", "r") as k:
            keys = json.load(k)
            
        self.dblpy = dbl.DBLClient(self.bot, keys["dblpy"])
        
        self.logger = logging.getLogger("Loops")
        self.logger.setLevel(logging.INFO)
        
    def cog_unload(self):
        self.bot.loop.create_task(self.stop_dblpy())
        
    async def stop_dblpy(self):
        await self.dblpy.close()
        
    async def updateTopGGStats(self):
        while True:
            await self.dblpy.post_guild_count()
            self.logger.info(" Updated Top.gg Stats")
            await asyncio.sleep(1800)
        
    async def updateActivity(self):
        while True:
            await self.bot.change_presence(activity=discord.Game(name=choice(self.g.playingList)))
            self.logger.info(" [SHARD {0}] Updated Activity".format(str(self.bot.shard_id)))
            await asyncio.sleep(3600)
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(self.updateActivity())
        self.bot.loop.create_task(self.updateTopGGStats())
        
def setup(bot):
    bot.add_cog(Loops(bot))