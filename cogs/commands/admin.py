from discord.ext import commands
import discord
import typing


class AdminCmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purge", aliases=["p"])
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def purgeLeMessages(self, ctx, message: typing.Union[int, str]=10):

        try:
            if isinstance(message, int):
                ctx.channel.purge(limit=message+1)
            elif isinstance(message, str):
                if message.lower() == 'all':
                    ctx.channel.purge()
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