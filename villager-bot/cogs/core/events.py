from discord.ext import commands
import time


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_shard_ready(self, shard_id: int):
        await self.bot.ipc.write_packet({"type": "shard-ready", "shard_id": shard_id})
        self.bot.logger.info(f"[Shard {shard_id}] \u001b[36;1mREADY\u001b[0m")

    @commands.Cog.listener()
    async def on_shard_disconnect(self, shard_id: int):
        await self.bot.ipc.write_packet({"type": "shard-disconnect", "shard_id": shard_id})


def setup(bot):
    bot.add_cog(Events(bot))
