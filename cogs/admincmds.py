from discord.ext import commands
import discord

class AdminCmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purge")
    @commands.has_permissions(administrator=True)
    async def purgeLeMessages(self, ctx, *, message: str):
        try:
            n = int(message)
        except Exception:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That is not a valid number!"))
        else:
            await ctx.channel.purge(limit=n+1)
            
    @commands.command(name="ban")
    @commands.has_permissions(administrator=True)
    async def banUser(self, ctx, *, user: discord.User):
        await ctx.guild.ban(user)
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Successfully banned **"+str(user)+"**."))

    @commands.command(name="pardon")
    @commands.has_permissions(administrator=True)
    async def pardonUser(self, ctx, *, user: discord.User):
        await ctx.guild.unban(user)
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Successfully unbanned **"+str(user)+"**."))

    @commands.command(name="kick")
    @commands.has_permissions(administrator=True)
    async def kickUser(self, ctx, *, user: discord.User):
        await ctx.guild.kick(user)
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Successfully kicked **"+str(user)+"**."))
        
def setup(bot):
    bot.add_cog(AdminCmds(bot))
