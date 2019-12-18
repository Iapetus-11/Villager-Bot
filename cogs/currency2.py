from discord.ext import commands, tasks
import discord
import dbl
import pymongo
import json

class Currency2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dbclient = pymongo.MongoClient("mongodb://MongoDB0:Crystal6@cluster0-22qio.mongodb.net")
        self.currency = self.dbclient["currency-db"]["currency"]
        self.test = self.dbclient.test
        
    @commands.command(name="boop")
    async def boop(self, ctx):
        for thing in self.test.find():
            await ctx.send(thing)
            
def setup(bot):
    bot.add_cog(Currency2(bot))
