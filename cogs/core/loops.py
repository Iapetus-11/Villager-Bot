from discord.ext import commands, tasks
import discord
import random


class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = bot.d

        self.change_status.start()
        self.update_fishing_prices.start()

    def cog_unload(self):
        self.change_status.cancel()
        self.update_fishing_prices.cancel()

    @tasks.loop(minutes=45)
    async def change_status(self):
        await self.bot.wait_until_ready()
        await self.bot.change_presence(activity=discord.Game(name=random.choice(self.d.playing_list)))

    @tasks.loop(hours=24)
    async def update_fishing_prices(self):
        self.bot.update_fishing_prices()


def setup(bot):
    bot.add_cog(Loops(bot))
