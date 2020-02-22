from discord.ext import commands
import discord
from random import choice

class Msgs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.msg_count = 0
        self.cmd_count = 0
        
    @commands.Cog.listener()
    async def on_message(self, message):
        self.msg_count += 1
        if message.content.startswith("!!"):
            self.cmd_count += 1
            await self.bot.get_cog("Currency").incrementMax(message)

def setup(bot):
    bot.add_cog(Msgs(bot))