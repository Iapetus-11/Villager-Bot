from discord.ext import commands
import discord


class AdminCmds(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purge", aliases=["p"])
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge_messages(self, ctx, n: int):
        if n <= 9999:
            try:
                await ctx.channel.purge(limit=n+1)
            except Exception:
                error_embed = discord.Embed(
                    color=discord.Color.green(),
                    description='''Uh oh, Villager Bot had a problem deleting those messages, try again later!''')
                await ctx.send(embed=error_embed)
        else:
            limit_embed = discord.Embed(
                color=discord.Color.green(),
                description='''You cannot purge more than 9999 messages at one time!''')
            await ctx.send(embed=limit_embed)

    @commands.command(name="ban")
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def ban_user(self, ctx, user: discord.User, *, reason="No reason provided."):
        for entry in await ctx.guild.bans():
            if entry[1].id == user.id:
                already_banned_embed = discord.Embed(
                    color=discord.Color.green(),
                    description="User has been already banned!")
                await ctx.send(embed=already_banned_embed)
                return

        await ctx.guild.ban(user, reason=reason)
        banned_embed = discord.Embed(
            color=discord.Color.green(),
            description=f"Successfully banned **{str(user)}**.")
        await ctx.send(embed=banned_embed)

    @commands.command(name="pardon")
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def pardon_user(self, ctx, user: discord.User, *, reason="No reason provided."):
        for entry in await ctx.guild.bans():
            if entry[1].id == user.id:
                await ctx.guild.unban(user, reason=reason)
                unban_embed = discord.Embed(
                    color=discord.Color.green(),
                    description=f"Successfully unbanned **{str(user)}**.")
                await ctx.send(embed=unban_embed)
                return

        not_banned_embed = discord.Embed(
            color=discord.Color.green(),
            description="Mentioned user had not been banned before!")
        await ctx.send(embed=not_banned_embed)

    @commands.command(name="kick")
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def kick_user(self, ctx, user: discord.User, *, reason="No reason provided."):
        await ctx.guild.kick(user, reason=reason)
        kick_embed = discord.Embed(
            color=discord.Color.green(),
            description=f"Successfully kicked **{str(user)}**.")
        await ctx.send(embed=kick_embed)

    @commands.command(name="warn")
    @commands.guild_only()
    @commands.check_any(commands.has_permissions(administrator=True), commands.has_permissions(kick_members=True), commands.has_permissions(ban_members=True))
    async def warn(self, user: discord.User, *, reason="No reason provided"):
        await self.db.add_warn()


def setup(bot):
    bot.add_cog(AdminCmds(bot))
