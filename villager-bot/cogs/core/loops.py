from discord.ext import commands, tasks
from classyjson import ClassyDict
import asyncio


class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.aiohttp = bot.aiohttp

    @tasks.loop(hours=1)
    async def update_minecraft_servers(self):
        """fetches the coolest mc servers from minecraft.global, and stores them for usage in !!randommc"""

        for i in range(0, 240, 24):  # .75 * 10 = 7.5 seconds + processing time this will be about as slow as scraping mclists *cry*
            res = await self.aiohttp.get(f"https://api.minecraft.global/search?amount=24&online=True&offset={i}")
            data = await res.json()

            servers = set()

            for e in data["payload"]["entries"]:
                if e.get("advertisement_id") is None:  # exclude advertisements
                    if e["port"]:  # get and format address
                        address = f"{e['host']}:{e['port']}"
                    else:
                        address = e["host"]

                    servers.add((address, e["server_id"]))

            self.bot.minecraft_servers.update(servers)

            await asyncio.sleep(.75)  # required to not hit the api ratelimits




def setup(bot):
    bot.add_cog(Loops(bot))
