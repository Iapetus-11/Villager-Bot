from discord.ext import commands, tasks
import discord
import random


class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.d = self.bot.d

        self.change_status.start()

    @tasks.loop(minutes=45)
    async def change_status(self):
        await self.bot.change_presence(activity=discord.Game(name=random.choice(self.d.playing_list)))

    @change_status.before_loop
    async def before_change_status(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Status(bot))
