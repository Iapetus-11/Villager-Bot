import random
from contextlib import suppress

import arrow
import discord
from discord.ext import commands, tasks

from bot.utils.setup import update_fishing_prices
from bot.villager_bot import VillagerBotCluster


class Loops(commands.Cog):
    def __init__(self, bot: VillagerBotCluster):
        self.bot = bot

        self.aiohttp = bot.aiohttp
        self.d = bot.d

        self.clear_rcon_cache.start()
        self.change_status.start()
        self.update_fishing_prices.start()

    def cog_unload(self):
        self.clear_rcon_cache.cancel()
        self.change_status.cancel()
        self.update_fishing_prices.cancel()

    @tasks.loop(minutes=45)
    async def change_status(self):
        await self.bot.wait_until_ready()
        await self.bot.change_presence(
            status=discord.Status.online,
            activity=discord.Game(name=random.choice(self.d.playing_list)),
        )

    @tasks.loop(seconds=30)
    async def clear_rcon_cache(self):
        """clear old connections from the rcon cache"""

        for key, connection in self.bot.rcon_cache.copy().items():
            if arrow.utcnow().shift(minutes=-1) > connection[1]:
                with suppress(Exception):
                    await connection[0].close()

                self.bot.rcon_cache.pop(key, None)

    @tasks.loop(hours=24)
    async def update_fishing_prices(self):
        update_fishing_prices(self.d)


async def setup(bot: VillagerBotCluster) -> None:
    bot.add_cog(Loops(bot))
