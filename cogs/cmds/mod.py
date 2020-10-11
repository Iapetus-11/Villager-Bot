from discord.ext import commands
from typing import Union
import discord


class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.d = self.bot.d

    async def perm_check(self, author, victim):
        if author.id == author.guild.owner.id: return True
        guild_roles = author.guild.roles
        return guild_roles.index(author.top_role) > guild_roles.index(
            victim.top_role) and not victim.id == author.guild.owner.id

    @commands.command(name='purge', aliases=['p'])
    @commands.guild_only()
    @commands.bot_has_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, to_purge: Union[discord.Member, int], amount=20):
        """Purges the given amount of messages from the current channel"""

        if type(to_purge) is discord.User:
            def check(m):
                return m.author.id == to_purge.id

            await ctx.channel.purge(check=check, limit=amount+1)
        else:
            await ctx.channel.purge(limit=to_purge+1)

    @commands.command(name='kick', aliases=['yeet'])
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick_user(self, ctx, user: discord.Member, *, reason='No reason provided.'):
        """Kicks the given user from the current Discord server"""

        if ctx.author.id == user.id:
            await ctx.send(embed=discord.Embed(color=self.d.cc, title=ctx.l.mod.kick.error))
            return

        if not await self.perm_check(ctx.author, user):
            await ctx.send(embed=discord.Embed(color=self.d.cc, title=ctx.l.mod.no_perms))
            return

        await ctx.guild.kick(user, reason=reason)
        await ctx.send(embed=discord.Embed(color=self.d.cc, title=ctx.l.mod.kick.success.format(user)))

    @commands.command(name='ban', aliases=['megayeet'])
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_user(self, ctx, user: Union[discord.Member, int], *, reason='No reason provided.'):
        """Bans the given user from the current Discord server"""

        if ctx.author.id == user.id:
            await ctx.send(embed=discord.Embed(color=self.d.cc, title=ctx.l.mod.ban.error_1))
            return

        if not await self.perm_check(ctx.author, user):
            await ctx.send(embed=discord.Embed(color=self.d.cc, title=ctx.l.mod.no_perms))
            return

        for entry in await ctx.guild.bans():
            if entry[1].id == user.id:
                await ctx.send(embed=discord.Embed(color=self.d.cc, title=ctx.l.mod.ban.error_2.format(user)))
                return

        try:
            await ctx.guild.ban(user, reason=reason, delete_message_days=0)
            await ctx.send(embed=discord.Embed(color=self.d.cc, title=ctx.l.mod.ban.success.format(user)))
        except Exception:
            await ctx.send(embed=discord.Embed(color=self.d.cc, title=ctx.l.mod.ban.error_3))

    @commands.command(name='pardon', aliases=['unban'])
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def pardon_user(self, ctx, user: discord.User, *, reason='No reason provided.'):
        """Unbans / pardons the given user from the current Discord server"""

        if ctx.author.id == user.id:
            await ctx.send(embed=discord.Embed(color=self.d.cc, title=ctx.l.mod.unban.error_1))
            return

        for entry in await ctx.guild.bans():
            if entry[1].id == user.id:
                await ctx.guild.unban(user, reason=reason)
                await ctx.send(embed=discord.Embed(color=self.d.cc, title=ctx.l.mod.unban.success.format(user)))
                return

        await ctx.send(embed=discord.Embed(color=self.d.cc, title=ctx.l.mod.unban.error_2.format(user)))

    @commands.command(name='warn')
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, user: discord.User):



def setup(bot):
    bot.add_cog(Mod(bot))
