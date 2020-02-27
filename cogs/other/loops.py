from discord.ext import commands
import discord
import asyncio
import logging

class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.g = self.bot.get_cog("Global")
        
        self.logger = logging.getLogger("Loops")
        self.logger.setLevel(logging.INFO)
        
    async def updateActivity(self):
        while True:
            await self.bot.change_presence(activity=discord.Game(name=choice(self.g.playingList)))
            await self.logger.info(" [SHARD {0}] Updated Activity".format(self.bot.shard_id))
            await asyncio.sleep(3600)
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(self.updateActivity())
        
def setup(bot):
    bot.add_cog(Loops(bot))