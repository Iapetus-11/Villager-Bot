from discord.ext import commands
import statcord


class StatCord(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.d = self.bot.d

        self.statcord_client = statcord.Client(bot, self.d.statcord_key)
        self.statcord_client.start_loop()

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.statcord_client.command_run(ctx)


def setup(bot):
    bot.add_cog(StatCord(bot))
