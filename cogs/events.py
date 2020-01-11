from discord.ext import commands
import discord
from random import choice
from time import sleep
import arrow
import asyncio

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(self.bot.user.name)
        print(self.bot.user.id)
        print(self.bot.shard_id)
        print("Successfully connected to Discord!"+"\n")
        with open("playing.txt", "r") as p:
            playing = p.readlines()
        await self.bot.change_presence(activity=discord.Game(name=choice(playing)))
        with open("uptime.txt", "w") as f:
            f.write(str(arrow.utcnow()))

    @commands.Cog.listener()
    async def on_guild_join(bot, guild):
        await asyncio.sleep(1)
        ret = False
        i = 0
        joinMsg = discord.Embed(color=discord.Color.green(), description="""Hey ya'll, type **!!help** to get started with Villager Bot!""")
        joinMsg.set_footer(text="Note: Bot errors caused by users are logged so the Villager Bot programmers can fix bugs!")
        while i >= 0:
            try:
                await guild.channels[i].send(embed=joinMsg)
            except Exception:
                i += 1
                pass
            else:
                i = -100
                
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if type(error) == discord.ext.commands.CommandNotFound or type(error) == discord.ext.commands.NotOwner or type(error) == discord.ext.commands.errors.CheckFailure: #errrors to ignore
            return
        
        if type(error) == discord.ext.commands.errors.MissingRequiredArgument:
            if str(ctx.command) == "gamble":
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Aren't you forgetting something? Perhaps you need to specify the quantity of emeralds to gamble with..."))
            elif str(ctx.command) == "battle" or str(ctx.command) == "pillage":
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Uh oh, the command didn't work. Maybe you should actually mention a person?"))
            elif str(ctx.command) == "give":
                if str(error.param) == "rec":
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Maybe you should tell me who to send the emeralds to, next time I'm keeping them!"))
                else:
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Look at that, you didn't specify how many emeralds to give, I'll just send them all."))
            elif str(ctx.command) == "kick" or str(ctx.command) == "ban" or str(ctx.command) == "pardon":
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Oh, would you look at that! You didn't tell me who to "+str(ctx.command)+"."))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="HRMMM, looks like you're forgetting to put something in!"))
            return
                
        elif type(error) == discord.ext.commands.CommandOnCooldown:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Didn't your parents tell you patience was a virtue? Calm down and wait another "+str(round(error.retry_after, 2))+" seconds."))
            return
            
        elif type(error) == discord.ext.commands.BadArgument:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Looks like you typed something wrong, try typing it correctly the first time, duh."))
            return
            
        elif type(error) == discord.ext.commands.MissingPermissions:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Nice try stupid, but you don't have the permissions to do that."))
            return
        
        elif type(error) == discord.ext.commands.BotMissingPermissions:
            try:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You didn't give me the permissions to do that, idiot."))
            except Exception:
                pass
            return
        
        elif "error code: 50013" in str(error):
            try:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="I can't do that, you idiot."))
            except Exception:
                pass
            return
            
        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["OH SNAP.", "OH FU\*\*.", "\*\*\*\*\*\*\*\*\*\*."])+" You found an actual error, please take a screenshot and report it on our [support server](https://discord.gg/39DwwUV). Thanks!"))
        
        channel = self.bot.get_channel(642446655022432267)
        await channel.send("```"+str(ctx.author)+": "+ctx.message.content+"\n\nError: "+str(error)+"\n\nType: "+str(type(error))+"```")
        
def setup(bot):
    bot.add_cog(Events(bot))