from discord.ext import commands
import discord
import logging


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = logging.getLogger("Events")
        self.logger.setLevel(logging.INFO)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(activity=discord.Game(name=choice(self.bot.playing_list)))
        self.logger.info(f"\u001b[36;1m CONNECTED \u001b[0m [{self.bot.shard_count} Shards] [{len(self.bot.cogs)} Cogs]")
        

def setup(bot):
    bot.add_cog(Events(bot))
