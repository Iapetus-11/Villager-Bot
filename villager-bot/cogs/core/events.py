from discord.ext import commands
import time


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_shard_ready(self, shard_id: int):
        self.bot.logger.info(f"[Shard {shard_id}] \u001b[36;1mCONNECTED\u001b[0m")


def setup(bot):
    bot.add_cog(Events(bot))
