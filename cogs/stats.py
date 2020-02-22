from discord.ext import commands
import discord

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.statz = {}
        
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.content.startswith("!!"):
            if message.author.id in self.statz.keys():
                self.statz[message.author.id] += 1
            else:
                self.statz[message.author.id] = 1
            
    @commands.command(name="statistics", aliases=["stats"])
    async def stats(self, ctx):
        i = 0
        rows = 35
        msg = ""
        for uid in self.statz:
            i += 1
            msg += "\n**"+str(self.statz[uid])+"** "+str(uid)
            if i%rows == 0:
                await ctx.send(msg)
                msg = ""
        if msg is not "":
            await ctx.send(msg)

def setup(bot):
    bot.add_cog(Stats(bot))