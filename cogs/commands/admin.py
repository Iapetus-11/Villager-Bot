from discord.ext import commands
import discord

class AdminCmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purge", aliases=["p"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def purgeLeMessages(self, ctx, *, message: str):
        try:
            n = int(message)
        except Exception:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That is not a valid number!"))
            return
        ch = await self.bot.fetch_channel(ctx.channel.id)
        try:
            await ch.purge(limit=n+1)
        except Exception:
            await ctx.send("Uh oh, Villager Bot had a problem deleting those messages, try again later!")
            
    @commands.command(name="ban")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def banUser(self, ctx, *, user: discord.User):
        for entry in await ctx.guild.bans():
            if entry[1].id == user.id: #apparently named tuples only take indexs and not slices like ["urmomgae"]
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="User has been already banned!"))
                return
        await ctx.guild.ban(user)
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Successfully banned **"+str(user)+"**."))

    @commands.command(name="pardon")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def pardonUser(self, ctx, *, user: discord.User):
        for entry in await ctx.guild.bans():
            if entry[1].id == user.id:
                await ctx.guild.unban(user)
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Successfully unbanned **"+str(user)+"**."))
                return
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Mentioned user had not been banned before!"))

    @commands.command(name="kick")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def kickUser(self, ctx, *, user: discord.User):
        await ctx.guild.kick(user)
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Successfully kicked **"+str(user)+"**."))
        
def setup(bot):
    bot.add_cog(AdminCmds(bot))