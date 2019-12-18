from discord.ext import commands, tasks
import discord
import asyncio
import json
import dbl
from random import choice

class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.token = json.load(open("keys.json", "r"))["dblpy"]
        self.dblpy = dbl.DBLClient(self.bot, self.token, webhook_path="/dblwebhook", webhook_auth="password", webhook_port=5000)

    async def activity(self):
        await asyncio.sleep(2)
        while not self.bot.is_closed():
            with open("playing.txt", "r") as file:
                playing = file.readlines()
            await self.bot.change_presence(activity=discord.Game(name=choice(playing)))
            print("ACTIVITY UPDATED")
            await asyncio.sleep(10800)
        
    async def topggstats(self):
        await asyncio.sleep(2)
        while not self.bot.is_closed():
            await self.dblpy.post_guild_count()
            print("DBL STATS UPDATED")
            await asyncio.sleep(1800)
            
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(self.activity())
        self.bot.loop.create_task(self.topggstats())
        
def setup(bot):
    bot.add_cog(Loops(bot))
