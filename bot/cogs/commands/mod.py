import asyncio
from typing import Union

import arrow
import discord
from discord.ext import commands

from bot.utils.ctx import Ctx
from bot.utils.misc import parse_input_time
from bot.villager_bot import VillagerBotCluster


class Mod(commands.Cog):
    def __init__(self, bot: VillagerBotCluster):
        self.bot = bot

        self.d = bot.d

        self.db = bot.get_cog("Database")

    def permission_check(self, ctx: Ctx, victim: discord.Member) -> bool:
        author = ctx.author

        if author == ctx.guild.owner:
            return True

        return author.top_role > victim.top_role

    @commands.command(name="purge", aliases=["p"])
    @commands.guild_only()
    @commands.bot_has_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: Ctx, amount: int):
        """Purges the given amount of messages from the current channel"""

        if amount < 1:
            return

        try:
            await ctx.channel.purge(limit=amount + 1)
        except asyncio.queues.QueueEmpty:
            await ctx.reply_embed(ctx.l.mod.purge.oop)
        except discord.errors.NotFound:
            await ctx.reply_embed(ctx.l.mod.purge.oop)

    @commands.command(name="kick", aliases=["yeet"])
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick_user(self, ctx: Ctx, victim: discord.Member, *, reason="No reason provided."):
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
    async def ban_user(
        self, ctx: Ctx, victim: Union[discord.Member, int], *, reason="No reason provided."
    ):
        """Bans the given user from the current Discord server"""

        delete_days = 0

        if isinstance(victim, int):
            if self.bot.get_user(victim) is None:
                try:
                    victim = await self.bot.fetch_user(victim)
                except discord.HTTPException:
                    raise commands.BadArgument
            else:
                victim = self.bot.get_user(victim)

        if ctx.author == victim:
            await ctx.reply_embed(ctx.l.mod.ban.stupid_1)
            return

        if isinstance(victim, discord.Member):
            if not self.permission_check(ctx, victim):
                await ctx.reply_embed(ctx.l.mod.no_perms)
                return

        try:
            await ctx.guild.fetch_ban(victim)
        except discord.NotFound:
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
            await ctx.guild.ban(
                victim, reason=f"{ctx.author} | {reason}", delete_message_days=delete_days
            )
            await ctx.message.add_reaction(self.d.emojis.yes)
        except discord.errors.Forbidden:
            await ctx.reply_embed(ctx.l.mod.ban.stupid_3)

    @commands.command(name="pardon", aliases=["unban"])
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def pardon_user(
        self, ctx: Ctx, user: Union[discord.User, int], *, reason="No reason provided."
    ):
        """Unbans / pardons the given user from the current Discord server"""

        if isinstance(user, int):
            if self.bot.get_user(user) is None:
                try:
                    user = await self.bot.fetch_user(user)
                except discord.HTTPException:
                    raise commands.BadArgument
            else:
                user = self.bot.get_user(user)

        if ctx.author == user:
            await ctx.reply_embed(ctx.l.mod.unban.stupid_1)
            return

        try:
            await ctx.guild.fetch_ban(user)
        except discord.NotFound:
            await ctx.reply_embed(ctx.l.mod.unban.stupid_2.format(user))
            return

        await ctx.guild.unban(user, reason=f"{ctx.author} | {reason}")
        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="warn")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx: Ctx, victim: discord.Member, *, reason=None):
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
                self.d.emojis.yes,
                victim.mention,
                len(warns) + 1,
                discord.utils.escape_markdown(str(reason)),
            ),
        )

    @commands.command(name="warns", aliases=["warnings", "karens"])
    @commands.guild_only()
    async def warnings(self, ctx: Ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author

        if ctx.author != user:
            if not self.permission_check(ctx, user):
                await ctx.reply_embed(ctx.l.mod.no_perms)
                return

        warns = await self.db.fetch_warns(user.id, ctx.guild.id)

        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(
            name=f"{user}'s warnings ({len(warns)} total):",
            icon_url=getattr(user.avatar, "url", None),
        )

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

    @commands.command(
        name="delwarns", aliases=["clearwarns", "remwarns", "removewarns", "delwarnings"]
    )
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def clear_warnings(self, ctx: Ctx, user: discord.Member):
        if ctx.author == user and ctx.guild.owner != ctx.author:
            await ctx.reply_embed(ctx.l.mod.warn.stupid_2)
            return

        if not self.permission_check(ctx, user):
            await ctx.reply_embed(ctx.l.mod.no_perms)
            return

        await self.db.clear_warns(user.id, ctx.guild.id)
        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="mute", aliases=["shutup", "silence", "shush", "stfu", "timeout"])
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx: Ctx, victim: discord.Member, *args: str):
        if ctx.author == victim:
            await ctx.reply_embed(ctx.l.mod.mute.stupid_1)
            return

        if not self.permission_check(ctx, victim):
            await ctx.reply_embed(ctx.l.mod.no_perms)
            return

        success, at, rest = parse_input_time(args)

        if not success:
            await ctx.reply_embed(ctx.l.mod.mute.stupid_2.format(ctx.prefix))
            return

        if at > arrow.utcnow().shift(days=27):
            await ctx.reply_embed(ctx.l.mod.mute.stupid_3)
            return

        await victim.timeout(duration=(at - arrow.utcnow()), reason=f"{ctx.author} | {rest}")

        await ctx.reply_embed(ctx.l.mod.mute.mute_msg.format(victim.mention))

    @commands.command(name="unmute", aliases=["unshut", "shutnt", "unstfu", "untimeout"])
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def unmute(self, ctx: Ctx, user: discord.Member):
        if ctx.author == user:
            await ctx.reply_embed(ctx.l.mod.unmute.stupid_1)
            return

        if not self.permission_check(ctx, user):
            await ctx.reply_embed(ctx.l.mod.no_perms)
            return

        if user.current_timeout is None:
            await ctx.reply_embed(ctx.l.mod.unmute.stupid_2.format(user.mention))
            return

        await user.timeout(duration=None, reason=str(ctx.author))

        await ctx.reply_embed(ctx.l.mod.unmute.unmute_msg.format(user.mention))


async def setup(bot: VillagerBotCluster) -> None:
    await bot.add_cog(Mod(bot))
