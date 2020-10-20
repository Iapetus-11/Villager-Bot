from discord.ext import commands
from typing import Union
import discord


class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.d = self.bot.d

        self.db = self.bot.get_cog('Database')

    async def perm_check(self, author, victim):
        if isinstance(author, discord.Member) and author.id == author.guild.owner.id: return True
        guild_roles = author.guild.roles
        return guild_roles.index(author.top_role) > guild_roles.index(
            victim.top_role) and not victim.id == author.guild.owner.id

    @commands.command(name='purge', aliases=['p'])
    @commands.guild_only()
    @commands.bot_has_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, to_purge: Union[discord.Member, int], amount=20):
        """Purges the given amount of messages from the current channel"""

        try:
            if isinstance(to_purge, discord.Member):
                def check(m):
                    return m.author.id == to_purge.id

                await ctx.channel.purge(check=check, limit=amount+1)
            else:
                await ctx.channel.purge(limit=to_purge+1)
        except asyncio.queues.QueueEmpty:
            await self.bot.send(ctx, ctx.l.mod.purge.oop)

    @commands.command(name='kick', aliases=['yeet'])
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick_user(self, ctx, user: discord.Member, *, reason='No reason provided.'):
        """Kicks the given user from the current Discord server"""

        if ctx.author.id == user.id:
            await self.bot.send(ctx, ctx.l.mod.kick.stupid_1)
            return

        if not await self.perm_check(ctx.author, user):
            await self.bot.send(ctx, ctx.l.mod.no_perms)
            return

        await ctx.guild.kick(user, reason=reason)
        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name='ban', aliases=['megayeet'])
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_user(self, ctx, user: discord.Member, *, reason='No reason provided.'):
        """Bans the given user from the current Discord server"""

        if ctx.author.id == user.id:
            await self.bot.send(ctx, ctx.l.mod.ban.stupid_1)
            return

        if not await self.perm_check(ctx.author, user):
            await self.bot.send(ctx, ctx.l.mod.no_perms)
            return

        for entry in await ctx.guild.bans():
            if entry[1].id == user.id:
                await self.bot.send(ctx, ctx.l.mod.ban.stupid_2.format(user))
                return

        try:
            await ctx.guild.ban(user, reason=reason, delete_message_days=0)
            await ctx.message.add_reaction(self.d.emojis.yes)
        except Exception:
            await self.bot.send(ctx, ctx.l.mod.ban.stupid_3)

    @commands.command(name='pardon', aliases=['unban'])
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def pardon_user(self, ctx, user: discord.User, *, reason='No reason provided.'):
        """Unbans / pardons the given user from the current Discord server"""

        if ctx.author.id == user.id:
            await self.bot.send(ctx, ctx.l.mod.unban.stupid_1)
            return

        for entry in await ctx.guild.bans():
            if entry[1].id == user.id:
                await ctx.guild.unban(user, reason=reason)
                await ctx.message.add_reaction(self.d.emojis.yes)
                return

        await self.bot.send(ctx, ctx.l.mod.unban.stupid_2.format(user))

    @commands.command(name='warn')
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, user: discord.Member, *, reason=None):
        if ctx.author.id == user.id:
            await self.bot.send(ctx, ctx.l.mod.warn.stupid_1)
            return

        if not await self.perm_check(ctx.author, user):
            await self.bot.send(ctx, ctx.l.mod.no_perms)
            return

        if reason is not None:
            if len(reason) > 245:
                reason = f'{reason[:245]}...'

        await self.db.add_warn(user.id, ctx.guild.id, ctx.author.id, reason)

        warns = await self.db.fetch_warns(user.id, ctx.guild.id)
        await self.bot.send(ctx, ctx.l.mod.warn.confirm.format(self.d.emojis.yes, user.mention, reason))

    @commands.command(name='warns', aliases=['warnings', 'karens'])
    @commands.guild_only()
    async def warnings(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author

        if ctx.author.id != user.id:
            if not await self.perm_check(ctx.author, user):
                await self.bot.send(ctx, ctx.l.mod.no_perms)
                return

        warns = await self.db.fetch_warns(user.id, ctx.guild.id)

        embed = discord.Embed(color=self.d.cc)
        embed.set_author(name=f'{user}\'s warnings ({len(warns)} total):', icon_url=user.avatar_url_as())

        if len(warns) < 1:
            embed.add_field(name='\uFEFF', value=f'{user} has no warnings.')
        else:
            for warn in warns:
                reason = ctx.l.mod.warn.no_reason

                if warn['reason'] is not None:
                    reason = warn['reason']

                embed.add_field(name='\uFEFF', value=f'**{ctx.l.mod.warn.by} {self.bot.get_user(warn["mod_id"]).mention}**: *{reason}*', inline=False)

        await ctx.send(embed=embed)

    @commands.command(name='delwarns', aliases=['clearwarns', 'remwarns', 'removewarns', 'delwarnings'])
    @commands.guild_only()
    async def clear_warnings(self, ctx, user: discord.Member):
        if ctx.author.id == user.id and ctx.guild.owner.id != ctx.author.id:
            await self.bot.send(ctx, ctx.l.mod.warn.stupid_1)
            return

        if not await self.perm_check(ctx.author, user):
            await self.bot.send(ctx, ctx.l.mod.no_perms)
            return

        await self.db.clear_warns(user.id, ctx.guild.id)
        await ctx.message.add_reaction(self.d.emojis.yes)

def setup(bot):
    bot.add_cog(Mod(bot))
