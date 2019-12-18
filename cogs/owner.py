from discord.ext import commands
import discord
from random import choice

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global msg_count
        msg_count = 0
        global cmd_count
        cmd_count = 0
        
    @commands.Cog.listener()
    async def on_message(self, message):
        global msg_count
        global cmd_count
        msg_count += 1
        if message.clean_content.startswith("!!"):
            cmd_count += 1
        
    @commands.command(name="ownerhelp", aliases=["helpowner", "owner"])
    @commands.is_owner()
    async def ownerhelp(self, ctx):
        embedMsg = discord.Embed(
            description = """
**!!unload** ***cog*** *unloads a cog*
**!!load** ***cog*** *loads a cog*
**!!reload** ***cog*** *reloads a cog, error if cog had not been loaded prior*
**!!activity** ***text*** *sets activity of bot to given text*
**!!nextactivity** *picks random activity from list*
**!!guilds** *lists guild member count, guild name, guild id*
**!!dms** *lists private channels (group msgs and dms)*
**!!leaveguild** ***guild id*** *leaves specified guild*
**!!getinvites** ***guild id*** *gets invite codes for specified guild*
**!!info2** *displays information about stuff*
**!!setbal** ***@user amount*** *set user balance to something*
**!!eval** ***statement*** *uses eval()*""",
            color = discord.Color.green()
        )
        embedMsg.set_author(name="Villager Bot Owner Commands", url=discord.Embed.Empty, icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
        await ctx.send(embed=embedMsg)

    @commands.command(name="unload")
    @commands.is_owner()
    async def unload(self, ctx, *, cog: str):
        try:
            self.bot.unload_extension("cogs."+cog)
        except Exception as e:
            await ctx.send("Error while unloading extension: "+cog+"\n``"+str(e)+"``")
            return
        await ctx.send("Successfully unloaded cog: "+cog)

    @commands.command(name="load")
    @commands.is_owner()
    async def load(self, ctx, *, cog: str):
        try:
            self.bot.load_extension("cogs."+cog)
        except Exception as e:
            await ctx.send("Error while loading extension: "+cog+"\n``"+str(e)+"``")
            return
        await ctx.send("Successfully loaded cog: "+cog)
            
    @commands.command(name="reload")
    @commands.is_owner()
    async def reload(self, ctx, *, cog: str):
        try:
            self.bot.unload_extension("cogs."+cog)
        except commands.ExtensionNotLoaded:
            pass
        except Exception as e:
            await ctx.send("Error while unloading extension: "+cog+"\n``"+str(e)+"``")
            return
        try:
            self.bot.load_extension("cogs."+cog)
        except Exception as e:
            await ctx.send("Error while loading extension: "+cog+"\n``"+str(e)+"``")
            return
        await ctx.send("Successfully reloaded cog: "+cog)

    @commands.command(name="activity")
    @commands.is_owner()
    async def activity(self, ctx, *, message: str):
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await self.bot.change_presence(activity=discord.Game(name=message))

    @commands.command(name="nextactivity")
    @commands.is_owner()
    async def nextactivity(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass
        playing = open("playing.txt", "r").readlines()
        await self.bot.change_presence(activity=discord.Game(name=choice(playing)))

    @commands.command(name="guilds")
    @commands.is_owner()
    async def guilds(self, ctx):
        i = 0
        rows = 32
        msg = ""
        for guild in self.bot.guilds:
            i += 1
            msg += "\n"+str(guild.member_count)+" **"+guild.name+"** *"+str(guild.id)+"*"
            if i%rows == 0:
                await ctx.send(msg)
                msg = ""
        if msg is not "":
            await ctx.send(msg)
            
    @commands.command(name="dms")
    @commands.is_owner()
    async def dmlist(self, ctx):
        i = 0
        rows = 30
        msg = ""
        for pchannel in self.bot.private_channels:
            i += 1
            try:
                msg += "\n*"+str(pchannel.id)+"*  "+str(pchannel)
            except Exception as e:
                msg += "\n"+str(e)
            if i%rows == 0:
                await ctx.send(msg)
                msg = ""
        if msg is not "":
            await ctx.send(msg)

    @commands.command(name="leaveguild")
    @commands.is_owner()
    async def leaveguild(self, ctx, *, guild: int):
        await self.bot.get_guild(guild).leave()
        
    @commands.command(name="getinvites")
    @commands.is_owner()
    async def getinvites(self, ctx, *, guild: int):
        invites = await self.bot.get_guild(guild).invites()
        i = 0
        rows = 30
        msg = ""
        for invite in invites:
            i += 1
            msg += "\n"+str(invite.code)
            if i%rows == 0:
                await ctx.send(msg)
                msg = ""
        if msg is not "":
            await ctx.send(msg)
        
    @commands.command(name="info2")
    @commands.is_owner()
    async def info2(self, ctx):
        global msg_count
        global cmd_count
        infoEmbed = discord.Embed(
            description = "",
            color = discord.Color.green()
        )
        infoEmbed.add_field(name="__**Owner Info**__", value="""
Guild Count: {0}
DM Channel Count: {1}
User Count: {2}
Session Message Count: {3}
Session Command Count: {4}
Shard Count: {5}
Latency: {6} ms
""".format(str(len(self.bot.guilds)), str(len(self.bot.private_channels)), str(len(self.bot.users)), msg_count, cmd_count, self.bot.shard_count, str(self.bot.latency*1000)[:5]))
        await ctx.send(embed=infoEmbed)
        
    @commands.command(name="eval")
    @commands.is_owner()
    async def evalMessage(self, ctx, *, msg):
        try:
            evalMsg = eval(msg)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=str(evalMsg)))
        except Exception as e:
            if type(e) == discord.HTTPException:
                if e.code == 50035:
                    with open("eval.txt", "w+") as evalF:
                        evalF.write(str(evalMsg))
                    with open("eval.txt", "r") as evalF:
                        await ctx.send(file=discord.File(evalF))
                else:
                    await ctx.send(str(e))
            else:
                await ctx.send(str(e))
                
    @commands.command(name="owo")
    @commands.is_owner()
    async def doopy(self, ctx, *, msg):
        await self.bot.get_guild(654273346577629193).channels[5].send(msg)
            
def setup(bot):
    bot.add_cog(Owner(bot))
