from discord.ext import commands
import discord


class AdminCmds(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.db = self.bot.get_cog("Database")

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
                    description='''Uh oh, Villager Bot had a problem deleting those messages, make sure I have manage message permissions!''')
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
        if ctx.author.id == user.id:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You cannot ban yourself."))
            return
        if ctx.author.top_role.id == user.top_role.id and ctx.author.id != ctx.guild.owner.id:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have the permissions to do that!"))
            return
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
        if ctx.author.id == user.id:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You cannot unban yourself."))
            return
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
        if ctx.author.id == user.id:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You cannot kick yourself."))
            return
        if ctx.author.top_role.id == user.top_role.id and ctx.author.id != ctx.guild.owner.id:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have the permissions to do that!"))
            return
        await ctx.guild.kick(user, reason=reason)
        kick_embed = discord.Embed(
            color=discord.Color.green(),
            description=f"Successfully kicked **{str(user)}**.")
        await ctx.send(embed=kick_embed)

    @commands.command(name="warn", aliases=["warnuser"])
    @commands.guild_only()
    @commands.check_any(commands.has_permissions(administrator=True), commands.has_permissions(kick_members=True), commands.has_permissions(ban_members=True))
    async def warn(self, ctx, user: discord.User, *, reason="No reason provided"):
        if ctx.author.id == user.id:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You cannot warn yourself."))
            return
        if ctx.author.top_role.id == user.top_role.id and ctx.author.id != ctx.guild.owner.id:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have the permissions to do that!"))
            return
        reason = (reason[:125] + "...") if len(reason) > 128 else reason
        await self.db.add_warn(user.id, ctx.author.id, ctx.guild.id, reason)
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"**{user}** was warned by **{ctx.author}** for reason: *{reason}*\n**{user}** now has {len(await self.db.get_warns(user.id, ctx.guild.id))} warning(s)."))

    @commands.command(name="warns", aliases=["getwarns", "getuserwarns", "warnings"])
    @commands.guild_only()
    @commands.check_any(commands.has_permissions(administrator=True), commands.has_permissions(kick_members=True), commands.has_permissions(ban_members=True))
    async def get_user_warns(self, ctx, user: discord.User):
        user_warns = await self.db.get_warns(user.id, ctx.guild.id)
        embed = discord.Embed(color=discord.Color.green(), title=f"**{user}**'s Warnings ({len(user_warns)} total):")
        if len(user_warns) == 0:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), title=f"**{user}**'s Warnings ({len(user_warns)} total):", description=f"**{user}** has no warnings in this server."))
            return
        for warning in user_warns:
            embed.add_field(name=f"Warning by **{self.bot.get_user(warning[1])}**:", value=warning[3], inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="clearwarns", aliases=["deletewarns", "removewarns"])
    @commands.guild_only()
    @commands.check_any(commands.has_permissions(administrator=True), commands.has_permissions(kick_members=True), commands.has_permissions(ban_members=True))
    async def clear_user_warns(self, ctx, user: discord.User):
        if ctx.author.id == user.id:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You can't clear your own warnings!"))
        if ctx.author.top_role.id == user.top_role.id and ctx.author.id != ctx.guild.owner.id:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have the permissions to do that!"))
            return
        user_warns = await self.db.get_warns(user.id, ctx.guild.id)
        if len(user_warns) == 0:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"**{user}** has no warns."))
        else:
            await self.db.clear_warns(user.id, ctx.guild.id)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"Cleared all of **{user}**'s warns."))


def setup(bot):
    bot.add_cog(AdminCmds(bot))
