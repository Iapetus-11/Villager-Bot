from discord.ext import commands
import discord
from random import choice
import asyncio
import logging
import dbl
import json

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.g = self.bot.get_cog("Global")
        self.db = self.bot.get_cog("Database")
        
        with open("data/keys.json", "r") as k:
            keys = json.load(k)
            
        self.dblpy = dbl.DBLClient(self.bot, keys["dblpy"], webhook_path='/dblwebhook', webhook_auth=keys["dblpy2"], webhook_port=5000)
        
        self.logger = logging.getLogger("Events")
        self.logger.setLevel(logging.INFO)
        
    def cog_unload(self):
        self.bot.loop.create_task(self.stop_dblpy())
        
    async def stop_dblpy(self):
        await self.dblpy.close()
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info(" \u001b[36;1mCONNECTED | Shard: "+str(self.bot.shard_id)+"\u001b[0m")
        await self.bot.change_presence(activity=discord.Game(name=choice(self.g.playingList)))

    @commands.Cog.listener()
    async def on_dbl_test(self, data):
        self.logger.info(" \u001b[35mDBL WEBHOOK TEST\u001b[0m")
        channel = self.bot.get_channel(643648150778675202)
        await channel.send(embed=discord.Embed(color=discord.Color.green(), description="DBL WEBHOOK TEST"))
    
    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        userID = int(data["user"])
        self.logger.info(" \u001b[32m;1m"+str(userID)+" VOTED ON TOP.GG\u001b[0m")
        multi = 1
        if await self.dblpy.get_weekend_status():
            multi = 2
        await self.db.setBal(userID, await self.db.getBal(userID)+(32*multi))
        user = self.bot.get_user(userID)
        await user.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["You have been awarded {0} <:emerald:653729877698150405> for voting for Villager Bot!",
                                                                                            "You have recieved {0} <:emerald:653729877698150405> for voting for Villager Bot!"]).format(32*multi)))
        await self.bot.get_channel(682195105784004610).send(":tada::tada::tada: "+user.display_name+" has voted! :tada::tada::tada:")
    
    @commands.Cog.listener()
    async def on_guild_join(bot, guild):
        await asyncio.sleep(1)
        ret = False
        i = 0
        joinMsg = discord.Embed(color=discord.Color.green(), description="Hey ya'll, type **!!help** to get started with Villager Bot!\n\n"+
                                "Want to recieve updates, report a bug, or make suggestions? Join the official [support server](https://discord.gg/39DwwUV)!")
        while i >= 0:
            try:
                await guild.channels[i].send(embed=joinMsg)
            except Exception:
                i += 1
                pass
            else:
                i = -100
        
def setup(bot):
    bot.add_cog(Events(bot))