from discord.ext import commands
import discord


class MobSpawning(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Do something with @on_message_event, maybe have dict with counters or somethin idk do algo depends on guild members there

def setup(bot):
    bot.add_cog(MobSpawning(bot))