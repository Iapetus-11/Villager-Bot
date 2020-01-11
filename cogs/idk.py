from discord.ext import commands
import discord
from random import choice
import asyncio

class Idk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="pwiizy")
    async def pwiizy(self, ctx):
        if ctx.guild is not None and ctx.guild.id == 539050002526240778:
            await ctx.send(choice(["Aww hell naw", "hell no", "Uhhh hell no", "hell naw", "heck no", "heqq no"]))
        
    @commands.command(name="daniel", aliases=["danieltjee"])
    async def daniel(self, ctx):
        if ctx.guild is not None and ctx.guild.id == 539050002526240778:
            await ctx.send(choice(["weeee", "weeeeeee", "weeeeeeeeeeeeeeeeeeeeeeee", "weeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"])+"\n\nhttps://www.youtube.com/channel/UChmkRFkzzzrmN4nAq6_7WeQ")
            
    @commands.command(name="warhammer")
    async def warhammer(self, ctx):
        if ctx.guild is not None and ctx.guild.id == 539050002526240778:
            thing = discord.Embed(color=discord.Color.green())
            thing.set_image(url="https://cdn.discordapp.com/attachments/652028930768764928/663504841322004490/sticc.png")
            await ctx.send(embed=thing)
    
def setup(bot):
    bot.add_cog(Idk(bot))