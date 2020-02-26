from discord.ext import commands
import discord
from random import choice

class Msgs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.get_cog("Database")
        self.msg_count = 0
        self.cmd_count = 0
        
    @commands.Cog.listener()
    async def on_message(self, message):
        self.msg_count += 1
        if message.content.startswith("!!"):
            self.cmd_count += 1
            await self.db.incrementVaultMax(message.author.id)

def setup(bot):
    bot.add_cog(Msgs(bot))