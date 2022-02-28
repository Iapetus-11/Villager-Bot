from disnake.ext import commands
from typing import Union
import asyncio
import disnake

from util.misc import SuppressCtxManager


class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = bot.d

        self.db = bot.get_cog("Database")

    def permission_check(self, ctx: commands.Context, victim: disnake.Member) -> bool:
        author = ctx.author

        if author == ctx.guild.owner:
            return True

        return author.top_role > victim.top_role

    @commands.command(name="purge", aliases=["p"])
    @commands.guild_only()
    @commands.bot_has_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        """Purges the given amount of messages from the current channel"""

        if amount < 1:
            return

        try:
            await ctx.channel.purge(limit=amount + 1)
        except asyncio.queues.QueueEmpty:
            await ctx.reply_embed(ctx.l.mod.purge.oop)
        except disnake.errors.NotFound:
            await ctx.reply_embed(ctx.l.mod.purge.oop)

    @commands.command(name="kick", aliases=["yeet"])
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick_user(self, ctx, victim: disnake.Member, *, reason="No reason provided."):
        """Kicks the given user from the current Discord server"""

        if ctx.author == victim:
            await ctx.reply_embed(ctx.l.mod.kick.stupid_1)
            return

        if not self.permission_check(ctx, victim):
            await ctx.reply_embed(ctx.l.mod.no_perms)
            return

        await ctx.guild.kick(victim, reason=f"{ctx.author} | {reason}")
        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="ban", aliases=["megayeet"])
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_user(self, ctx, victim: Union[disnake.Member, int], *, reason="No reason provided."):
        """Bans the given user from the current Discord server"""

        delete_days = 0

        if isinstance(victim, int):
            if self.bot.get_user(victim) is None:
                try:
                    victim = await self.bot.fetch_user(victim)
                except disnake.HTTPException:
                    raise commands.BadArgument
            else:
                victim = self.bot.get_user(victim)

        if ctx.author == victim:
            await ctx.reply_embed(ctx.l.mod.ban.stupid_1)
            return

        if isinstance(victim, disnake.Member):
            if not self.permission_check(ctx, victim):
                await ctx.reply_embed(ctx.l.mod.no_perms)
                return

        try:
            await ctx.guild.fetch_ban(victim)
        except disnake.NotFound:
            pass
        else:
            await ctx.reply_embed(ctx.l.mod.ban.stupid_2.format(victim))
            return

        reason_split = reason.split()

        if reason_split[0].isnumeric():
            delete_days = int(float(reason_split[0]))
            reason = " ".join(reason_split[1:])

        if not reason:
            reason = "No reason provided."

        try:
            await ctx.guild.ban(victim, reason=f"{ctx.author} | {reason}", delete_message_days=delete_days)
            await ctx.message.add_reaction(self.d.emojis.yes)
        except disnake.errors.Forbidden:
            await ctx.reply_embed(ctx.l.mod.ban.stupid_3)

    @commands.command(name="pardon", aliases=["unban"])
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def pardon_user(self, ctx, user: Union[disnake.User, int], *, reason="No reason provided."):
        """Unbans / pardons the given user from the current Discord server"""

        if isinstance(user, int):
            if self.bot.get_user(user) is None:
                try:
                    user = await self.bot.fetch_user(user)
                except disnake.HTTPException:
                    raise commands.BadArgument
            else:
                user = self.bot.get_user(user)

        if ctx.author == user:
            await ctx.reply_embed(ctx.l.mod.unban.stupid_1)
            return

        try:
            await ctx.guild.fetch_ban(user)
        except disnake.NotFound:
            await ctx.reply_embed(ctx.l.mod.unban.stupid_2.format(user))
            return

        await ctx.guild.unban(user, reason=f"{ctx.author} | {reason}")
        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="warn")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, victim: disnake.Member, *, reason=None):
        if ctx.author == victim:
            await ctx.reply_embed(ctx.l.mod.warn.stupid_1)
            return

        if not self.permission_check(ctx, victim):
            await ctx.reply_embed(ctx.l.mod.no_perms)
            return

        warns = await self.db.fetch_warns(victim.id, ctx.guild.id)

        if len(warns) >= 20:
            await ctx.reply_embed(ctx.l.mod.warn.thats_too_much_man)
            return

        if reason is not None:
            if len(reason) > 245:
                reason = f"{reason[:245]}..."

        await self.db.add_warn(victim.id, ctx.guild.id, ctx.author.id, reason)

        await ctx.reply_embed(
            ctx.l.mod.warn.confirm.format(
                self.d.emojis.yes, victim.mention, len(warns) + 1, disnake.utils.escape_markdown(str(reason))
            ),
        )

    @commands.command(name="warns", aliases=["warnings", "karens"])
    @commands.guild_only()
    async def warnings(self, ctx, user: disnake.Member = None):
        if user is None:
            user = ctx.author

        if ctx.author != user:
            if not self.permission_check(ctx, user):
                await ctx.reply_embed(ctx.l.mod.no_perms)
                return

        warns = await self.db.fetch_warns(user.id, ctx.guild.id)

        embed = disnake.Embed(color=self.d.cc)
        embed.set_author(name=f"{user}'s warnings ({len(warns)} total):", icon_url=getattr(user.avatar, "url", None))

        if len(warns) < 1:
            embed.add_field(name="\uFEFF", value=f"{user} has no warnings.")
        else:
            for warn in warns:
                reason = ctx.l.mod.warn.no_reason

                if warn["reason"] is not None:
                    reason = warn["reason"]

                embed.add_field(
                    name="\uFEFF",
                    value=f'**{ctx.l.mod.warn.by} {getattr(self.bot.get_user(warn["mod_id"]), "mention", "Unknown User")}**: *{reason}*',
                    inline=False,
                )

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="delwarns", aliases=["clearwarns", "remwarns", "removewarns", "delwarnings"])
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def clear_warnings(self, ctx, user: disnake.Member):
        if ctx.author == user and ctx.guild.owner != ctx.author:
            await ctx.reply_embed(ctx.l.mod.warn.stupid_2)
            return

        if not self.permission_check(ctx, user):
            await ctx.reply_embed(ctx.l.mod.no_perms)
            return

        await self.db.clear_warns(user.id, ctx.guild.id)
        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="mute", aliases=["shutup", "silence", "shush", "stfu"])
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, victim: disnake.Member):
        if ctx.author == victim:
            await ctx.reply_embed(ctx.l.mod.mute.stupid_1)
            return

        if not self.permission_check(ctx, victim):
            await ctx.reply_embed(ctx.l.mod.no_perms)
            return

        if disnake.utils.get(ctx.guild.roles, name="Muted") is None:  # check if role exists
            await ctx.guild.create_role(
                name="Muted", permissions=disnake.Permissions(send_messages=False, add_reactions=False)
            )

        # fetch role
        mute = disnake.utils.get(ctx.guild.roles, name="Muted")
        if mute is None:
            mute = disnake.utils.get(await ctx.guild.fetch_roles(), name="Muted")

        async with SuppressCtxManager(ctx.typing()):
            for channel in ctx.guild.text_channels:  # fix perms for channels
                if mute not in channel.overwrites:
                    await channel.set_permissions(mute, send_messages=False, add_reactions=False)

        await victim.add_roles(mute)
        await self.db.mute_user(victim.id, ctx.guild.id)
        await ctx.reply_embed(ctx.l.mod.mute.mute_msg.format(victim))

    @commands.command(name="unmute", aliases=["unshut", "shutnt", "unstfu"])
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def unmute(self, ctx, user: disnake.Member):
        if ctx.author == user:
            await ctx.reply_embed(ctx.l.mod.unmute.stupid_1)
            return

        if not self.permission_check(ctx, user):
            await ctx.reply_embed(ctx.l.mod.no_perms)
            return

        mute = disnake.utils.get(user.roles, name="Muted")

        if mute:
            await user.remove_roles(mute)
            await self.db.unmute_user(user.id, ctx.guild.id)
            await ctx.reply_embed(ctx.l.mod.unmute.unmute_msg.format(user))
        else:
            await ctx.reply_embed(ctx.l.mod.unmute.stupid_2.format(user))


def setup(bot):
    bot.add_cog(Mod(bot))
