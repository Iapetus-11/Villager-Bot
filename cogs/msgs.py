from discord.ext import commands
import discord
from random import choice

class Msgs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            print(str(message.author)+": "+str(message.content))
        except Exception:
            print(str(message.author)+":")
            
        if "emerald" in message.clean_content.lower():
            if message.author.id != 639498607632056321:
                await message.channel.send(choice(["hrmm", "hrmmm", "HRHHRMM", "hruhrmm", "hrmMrmm", "hrmmmm"]))

def setup(bot):
    bot.add_cog(Msgs(bot))