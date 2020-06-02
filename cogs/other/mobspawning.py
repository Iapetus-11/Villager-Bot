from discord.ext import commands
import discord
from random import choice, randint


class MobSpawning(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # "mobname": [actualname, health, ]
        murl = "http://olimone.ddns.net/images/mob_spawns/"
        self.mobs = {"zombie": ["zombie", 20, murl+"zombie.png"], "spider": ["spider", 16, murl+"spider.png"], "skeleton": ["skeleton", 20, murl+"skeleton.png"],
                     "creeper": ["creeper", 20, murl+"creeper.png"], "cave_spider": ["cave spider", 12, murl+"cave_spider.png"]}

    # also have random pillager events where server is ransacked
    async def spawn_event(self, gid): # Fuck me in the balls, wait don't how is that even possible?!
        mob = choice(list(self.mobs))

    @commands.Cog.listener()
    async def on_message(self, msg):
        if randint(0, msg.guild.member_count*100) in range(0, 100, 1): # WHAT THE FUCK IS THIS?
            if await self.db.get_difficulty(msg.channel.guild.id) != "peaceful":
                await self.spawn_event(msg.guild.id)


def setup(bot):
    bot.add_cog(MobSpawning(bot))
