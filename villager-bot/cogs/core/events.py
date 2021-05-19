from discord.ext import commands
import time


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        startup_time = round(time.time() - self.bot.start_time, 2)
        self.bot.logger.info(f"\u001b[36;1mCONNECTED\u001b[0m ({startup_time} seconds)")


def setup(bot):
    bot.add_cog(Events(bot))
