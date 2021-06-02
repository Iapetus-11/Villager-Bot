from discord.ext import commands, tasks
from classyjson import ClassyDict
import asyncio
import arrow


class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.aiohttp = bot.aiohttp

    @tasks.loop(seconds=30)
    async def clear_rcon_cache(self):
        """clear old connections from the rcon cache"""

        for key, connection in self.bot.rcon_cache.copy().items():
            if arrow.utcnow().shift(minutes=-1) > connection[1]:
                try:
                    await connection[0].close()
                except Exception:
                    pass

                self.bot.rcon_cache.pop(key, None)

    @tasks.loop(hours=1)
    async def update_minecraft_servers(self):
        """fetches the coolest mc servers from minecraft.global, and stores them for usage in !!randommc"""

        servers = set()

        # .75 * 10 = 7.5 seconds + processing time this will be about as slow as scraping mclists *cry*
        for i in range(0, 240, 24):
            res = await self.aiohttp.get(f"https://api.minecraft.global/search?amount=24&online=True&offset={i}")
            data = await res.json()

            for e in data["payload"]["entries"]:
                if e.get("advertisement_id") is None:  # exclude advertisements
                    if e["port"]:  # get and format address
                        address = f"{e['host']}:{e['port']}"
                    else:
                        address = e["host"]

                    servers.add((address, e["server_id"]))

            self.bot.minecraft_servers = list(servers)

            await asyncio.sleep(0.75)  # required to not hit the api ratelimits (yes it's .25 extra just to be nice to API)


def setup(bot):
    bot.add_cog(Loops(bot))
