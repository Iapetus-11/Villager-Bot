from discord.ext import commands, tasks
import arrow


class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.aiohttp = bot.aiohttp

        self.clear_rcon_cache.start()
        self.update_minecraft_servers.start()

    def cog_unload(self):
        self.clear_rcon_cache.cancel()
        self.update_minecraft_servers.cancel()

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

    @tasks.loop(minutes=30)
    async def update_minecraft_servers(self):
        """fetches all server ids from minecraft.global, and stores them for usage in !!randommc"""

        res = await self.aiohttp.get("https://api.minecraft.global/servers")
        self.bot.minecraft_server_ids = (await res.json())["payload"]


def setup(bot):
    bot.add_cog(Loops(bot))
