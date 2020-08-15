from discord.ext import commands
import discord
import logging
import random


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.d = self.bot.d

        self.logger = logging.getLogger("Events")
        self.logger.setLevel(logging.INFO)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(activity=discord.Game(name=random.choice(self.d.playing_list)))
        self.logger.info(f"\u001b[36;1m CONNECTED \u001b[0m [{self.bot.shard_count} Shards] [{len(self.bot.cogs)} Cogs]")

    @commands.Cog.listener()
    async def on_message(self, m):
        if '@someone' in m.content and m.guild is not None:
            someones = [u for u in m.guild.members if (not u.bot and u.status == discord.Status.online)]
            if len(someones) > 0:
                await m.channel.send(random.choice(someones).mention)


def setup(bot):
    bot.add_cog(Events(bot))
