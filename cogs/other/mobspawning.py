from discord.ext import commands
import discord
from random import choice, randint


class MobSpawning(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # "mobname": [img_url, health, ]
        self.mobs = {"zombie": []}

    async def spawn_event(self, gid): # Fuck me in the balls, wait don't how is that even possible?!
        mob = choice(list(self.mobs))

    @commands.Cog.listener()
    async def on_message(self, msg):
        if randint(0, msg.guild.member_count*100) in range(0, 100, 1): # WHAT THE FUCK IS THIS?
            if await self.db.get_difficulty(msg.channel.guild.id) != "peaceful":
                await self.spawn_event(msg.guild.id)


def setup(bot):
    bot.add_cog(MobSpawning(bot))
