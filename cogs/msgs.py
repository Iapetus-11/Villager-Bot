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
            
        if "emerald" in message.clean_content.lower():
            if message.author.id != 639498607632056321:
                try:
                    await message.channel.send(choice(["hrmm", "hrmmm", "HRHHRMM", "hruhrmm", "hrmMrmm", "hrmmmm"]))
                except Exception:
                    pass

def setup(bot):
    bot.add_cog(Msgs(bot))