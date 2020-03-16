from discord.ext import commands
import discord
from random import choice

class Msgs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.get_cog("Database")
        self.g = self.bot.get_cog("Global")
        
    async def send(self, ctx, msg):
        try:
            await ctx.send(msg)
        except Exception:
            pass
        
    @commands.Cog.listener()
    async def on_message(self, message):
        self.g.msg_count += 1
        await self.db.incrementVaultMax(message.author.id)
        
        if "emerald" in message.clean_content.lower() or "villager bot" in message.clean_content.lower():            
            if not message.guild is None and await self.db.getDoReplies(message.guild.id):
                await self.send(message.channel, choice(["hrmm", "hmm", "hrmmm", "hrghhmmm", "hrhhmmmmmmmmm", "hrmmmmmm", "hrmmmmmmmmmm", "hrmmmmm"]))
            else:
                await self.send(message.channel, choice(["hrmm", "hmm", "hrmmm", "hrghhmmm", "hrhhmmmmmmmmm", "hrmmmmmm", "hrmmmmmmmmmm", "hrmmmmm"]))
                
def setup(bot):
    bot.add_cog(Msgs(bot))