from discord.ext import commands


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Owner(bot))
