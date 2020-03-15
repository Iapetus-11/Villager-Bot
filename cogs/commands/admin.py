from discord.ext import commands
import discord
import typing


class AdminCmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purge", aliases=["p"])
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purgeLeMessages(self, ctx, n: int):
        if n < 999:
            try:
                await ctx.channel.purge(n+1)
            except Exception:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Uh oh, Villager Bot had a problem deleting those messages, try again later!"))
        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You cannot purge more than 999 messages at one time!"))
            
    @commands.command(name="ban")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def banUser(self, ctx, *, user: discord.User):
        for entry in await ctx.guild.bans():
            if entry[1].id == user.id:  # Apparently named tuples only take indices and not slices like ["urmomgae"]
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="User has been already banned!"))
                return
        await ctx.guild.ban(user)
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"Successfully banned **{str(user)}**."))

    @commands.command(name="pardon")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def pardonUser(self, ctx, *, user: discord.User):
        for entry in await ctx.guild.bans():
            if entry[1].id == user.id:
                await ctx.guild.unban(user)
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"Successfully unbanned **{str(user)}**."))
                return
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Mentioned user had not been banned before!"))

    @commands.command(name="kick")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def kickUser(self, ctx, *, user: discord.User):
        await ctx.guild.kick(user)
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"Successfully kicked **{str(user)}**."))


def setup(bot):
    bot.add_cog(AdminCmds(bot))
