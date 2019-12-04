from discord.ext import commands
import discord

class AdminCmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="adminhelp", aliases=["admincmds", "helpadmin"])
    @commands.has_permissions(administrator=True)
    async def adminCommands(self, ctx):
        helpMsg = discord.Embed(
            description = "",
            color = discord.Color.green()
        )
        helpMsg.add_field(name="__Admin Bot Commands__", value="""
**!!purge** ***number of messages*** *deletes n number of messages in the channel it's summoned in*
**!!kick** ***@user*** *kicks the mentioned user*
**!!ban** ***@user*** *bans the mentioned user*
**!!pardon** ***@user*** *unbans the mentioned user*
    """)
        await ctx.send(embed=helpMsg)

    @commands.command(name="purge")
    @commands.has_permissions(administrator=True)
    async def purgeMessages(self, ctx, *, message: str):
        try:
            n = int(message)
        except Exception:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That is not a valid number!"))
        else:
            await ctx.channel.purge(limit=n+1)
            
    @commands.command(name="ban")
    @commands.has_permissions(administrator=True)
    async def banUser(self, ctx, *, user: discord.User):
        try:
            await ctx.guild.ban(user)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Successfully banned **"+str(user)+"**."))
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Bot does not have proper permissions."))
        except discord.HTTPException:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="An error occured while banning user."))

    @commands.command(name="pardon")
    @commands.has_permissions(administrator=True)
    async def pardonUser(self, ctx, *, user: discord.User):
        try:
            await ctx.guild.unban(user)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Successfully unbanned **"+str(user)+"**."))
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Bot does not have proper permissions."))
        except discord.HTTPException:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="An error occured while unbanning user."))

    @commands.command(name="kick")
    @commands.has_permissions(administrator=True)
    async def kickUser(self, ctx, *, user: discord.User):
        try:
            await ctx.guild.kick(user)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Successfully kicked **"+str(user)+"**."))
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Bot does not have proper permissions."))
        except discord.HTTPException:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="An error occured while kicking user."))
        
def setup(bot):
    bot.add_cog(AdminCmds(bot))
