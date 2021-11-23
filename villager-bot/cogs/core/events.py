from discord.ext import commands
from contextlib import suppress
import asyncio
import discord
import random
import sys

from util.cooldowns import CommandOnKarenCooldown, MaxKarenConcurrencyReached
from util.misc import update_support_member_role
from util.code import format_exception
from util.ipc import PacketType


IGNORED_ERRORS = (commands.CommandNotFound, commands.NotOwner)

NITRO_BOOST_MESSAGES = {
    discord.MessageType.premium_guild_subscription,
    discord.MessageType.premium_guild_tier_1,
    discord.MessageType.premium_guild_tier_2,
    discord.MessageType.premium_guild_tier_3,
}

BAD_ARG_ERRORS = (
    commands.BadArgument,
    commands.errors.UnexpectedQuoteError,
    commands.errors.ExpectedClosingQuoteError,
    commands.errors.BadUnionArgument,
)

INVISIBLITY_CLOAK = ("||||\u200B" * 200)[2:-3]


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = bot.logger
        self.ipc = bot.ipc
        self.d = bot.d
        self.k = bot.k
        self.db = bot.get_cog("Database")

        bot.event(self.on_error)  # discord.py's Cog.listener() doesn't work for on_error events

    @property
    def badges(self):
        return self.bot.get_cog("Badges")

    async def filter_keywords(self, message) -> bool:
        """Returns True if there was a found keyword."""

        if len(message.content) <= 2:
            return False

        filtered_words = self.bot.filter_words_cache.get(message.guild.id)

        if filtered_words:
            for word in filtered_words:
                if word in message.content:
                    await message.delete()
                    return True

        return False

    async def on_error(self, event, *args, **kwargs):  # logs errors in events, such as on_message
        self.bot.error_count += 1

        exception = sys.exc_info()[1]
        traceback = format_exception(exception).replace("```", "｀｀｀")

        event_call_repr = f"{event}({',  '.join(list(map(repr, args)) + [f'{k}={repr(v)}' for k, v in kwargs.items()])})"
        self.logger.error(f"An exception occurred in this call:\n{event_call_repr}\n\n{traceback}")

        await self.bot.after_ready_ready.wait()
        await self.bot.error_channel.send(f"```py\n{event_call_repr[:100]}``````py\n{traceback[:1880]}```")

    @commands.Cog.listener()
    async def on_shard_ready(self, shard_id: int):
        await self.ipc.send({"type": PacketType.SHARD_READY, "shard_id": shard_id})
        self.bot.logger.info(f"Shard {shard_id} \u001b[36;1mREADY\u001b[0m")

    @commands.Cog.listener()
    async def on_shard_disconnect(self, shard_id: int):
        await self.ipc.send({"type": PacketType.SHARD_DISCONNECT, "shard_id": shard_id})

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.support_server = await self.bot.fetch_guild(self.d.support_server_id)

        self.bot.error_channel = await self.bot.fetch_channel(self.d.error_channel_id)
        self.bot.vote_channel = await self.bot.fetch_channel(self.d.vote_channel_id)

        self.bot.after_ready_ready.set()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await asyncio.sleep(1)

        channel = None

        for c in guild.text_channels:
            c_name = c.name.lower()

            if "general" in c_name or "chat" in c_name:
                channel = c
                break

        if channel is None:
            for c in guild.text_channels:
                if c.permissions_for(guild.me).send_messages:
                    channel = c
                    break

        if channel is None:
            return

        embed = discord.Embed(
            color=self.d.cc,
            description=f"Hey y'all! Type `{self.d.default_prefix}help` to get started with Villager Bot!\n"
            f"If you need any more help, check out the **[Support Server]({self.d.support})**!\n\n"
            f"*Our privacy policy can be found [here]({self.d.privacy_policy}).*",
        )

        embed.set_author(name="Villager Bot", icon_url=self.d.splash_logo)
        embed.set_footer(
            text=f"Made by Iapetus11 and others ({self.d.default_prefix}credits)  |  Check the {self.d.default_prefix}rules"
        )

        with suppress(discord.errors.Forbidden):
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if await self.db.fetch_user_muted(member.id, member.guild.id):
            with suppress(discord.errors.Forbidden, discord.errors.HTTPException):
                # fetch role
                mute = discord.utils.get(member.guild.roles, name="Muted")
                if mute is None:
                    mute = discord.utils.get(await member.guild.fetch_roles(), name="Muted")

                await member.add_roles(mute)

        if member.guild.id == self.d.support_server_id:
            await update_support_member_role(self.bot, member)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.guild.id == self.d.support_server_id:
            if before.roles != after.roles:
                await self.db.fetch_user(after.id)  # ensure user is in db

                role_names = {r.name for r in after.roles}

                await self.badges.update_user_badges(
                    after.id,
                    code_helper=("Code Helper" in role_names),
                    design_helper=("Design Helper" in role_names),
                    bug_smasher=("Bug Smasher" in role_names),
                    translator=("Translator" in role_names),
                )

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if after.guild:
            await self.filter_keywords(after)

    @commands.Cog.listener()
    async def on_message(self, message):
        self.bot.message_count += 1

        if message.author.bot:
            return

        if isinstance(message.channel, discord.DMChannel):
            await self.ipc.send({"type": PacketType.DM_MESSAGE, "user_id": message.author.id, "content": message.content})

            with suppress(discord.errors.Forbidden, discord.errors.HTTPException):
                prior_messages = len(await message.channel.history(limit=1, before=message).flatten())

                if prior_messages < 1:
                    embed = discord.Embed(
                        color=self.d.cc,
                        description=f"Hey {message.author.mention}! Type `{self.d.default_prefix}help` to get started with Villager Bot!\n"
                        f"If you need any more help, check out the **[Support Server]({self.d.support})**!",
                    )

                    embed.set_author(name="Villager Bot", icon_url=self.d.splash_logo)
                    embed.set_footer(
                        text=f"Made by Iapetus11 and others ({self.d.default_prefix}credits)  |  Check the {self.d.default_prefix}rules"
                    )

                    await message.channel.send(embed=embed)
        else:
            if await self.filter_keywords(message):
                return

        if message.content.startswith(f"<@!{self.bot.user.id}>") or message.content.startswith(f"<@{self.bot.user.id}>"):
            if message.guild is None:
                prefix = self.d.default_prefix
            else:
                prefix = self.bot.prefix_cache.get(message.guild.id, self.d.default_prefix)

            lang = self.bot.get_language(message)

            embed = discord.Embed(color=self.d.cc, description=lang.misc.pingpong.format(prefix, self.d.support))
            embed.set_author(name="Villager Bot", icon_url=self.d.splash_logo)
            embed.set_footer(text=lang.useful.credits.foot.format(prefix))

            with suppress(discord.errors.Forbidden, discord.errors.HTTPException):
                await message.channel.send(embed=embed)

            return

        if message.guild is None:
            return

        if message.guild.id == self.d.support_server_id:
            if message.type in NITRO_BOOST_MESSAGES:
                await self.db.add_item(message.author.id, "Barrel", 1024, 1)
                await self.bot.send_embed(
                    message.author, "Thanks for boosting the support server! You've received 1x **Barrel**!"
                )

                return

        content_lower = message.content.lower()

        if "@someone" in content_lower:
            someones = [
                u
                for u in message.guild.members
                if (
                    not u.bot
                    and u.status == discord.Status.online
                    and message.author.id != u.id
                    and u.permissions_in(message.channel).read_messages
                )
            ]

            if len(someones) > 0:
                with suppress(discord.errors.Forbidden, discord.errors.HTTPException):
                    await message.channel.send(
                        f"@someone {INVISIBLITY_CLOAK} {random.choice(someones).mention} {message.author.mention}"
                    )

                return

        if message.guild.id in self.bot.replies_cache:
            prefix = self.bot.prefix_cache.get(message.guild.id, self.d.default_prefix)

            if not message.content.startswith(prefix):
                with suppress(discord.errors.Forbidden, discord.errors.HTTPException):
                    if "emerald" in content_lower:
                        await message.channel.send(random.choice(self.d.hmms))
                    elif "creeper" in content_lower:
                        await message.channel.send("awww{} man".format(random.randint(1, 5) * "w"))
                    elif "reee" in content_lower:
                        await message.channel.send(random.choice(self.d.emojis.reees))
                    elif "amogus" in content_lower or content_lower == "sus":
                        await message.channel.send(self.d.emojis.amogus)
                    elif content_lower == "good bot":
                        await message.reply(random.choice(self.d.owos), mention_author=False)

    async def handle_cooldown(self, ctx, remaining: float, karen_cooldown: bool) -> None:
        if ctx.command.name == "mine":
            if await self.db.fetch_item(ctx.author.id, "Efficiency I Book") is not None:
                remaining -= 0.5

            active_effects = (await self.ipc.eval(f"active_effects.get({ctx.author.id})")).result

            if active_effects:
                if "haste ii potion" in active_effects:
                    remaining -= 1
                elif "haste i potion" in active_effects:
                    remaining -= 0.5

        seconds = round(remaining, 2)

        if seconds <= 0.05:
            if karen_cooldown:
                await self.ipc.send({"type": PacketType.COOLDOWN_ADD, "command": ctx.command.name, "user_id": ctx.author.id})

            await ctx.reinvoke()
            return

        hours = int(seconds / 3600)
        minutes = int(seconds / 60) % 60
        time = ""

        seconds -= round((hours * 60 * 60) + (minutes * 60), 2)

        if hours == 1:
            time += f"{hours} {ctx.l.misc.time.hour}, "
        elif hours > 0:
            time += f"{hours} {ctx.l.misc.time.hours}, "

        if minutes == 1:
            time += f"{minutes} {ctx.l.misc.time.minute}, "
        elif minutes > 0:
            time += f"{minutes} {ctx.l.misc.time.minutes}, "

        if seconds == 1:
            time += f"{round(seconds, 2)} {ctx.l.misc.time.second}"
        elif seconds > 0:
            time += f"{round(seconds, 2)} {ctx.l.misc.time.seconds}"

        await ctx.reply_embed(random.choice(ctx.l.misc.cooldown_msgs).format(time), ignore_exceptions=True)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, e: Exception):
        self.bot.error_count += 1

        if hasattr(ctx, "custom_error"):
            e = ctx.custom_error

        if not isinstance(e, MaxKarenConcurrencyReached):
            await self.ipc.send(
                {"type": PacketType.CONCURRENCY_RELEASE, "command": str(ctx.command), "user_id": ctx.author.id}
            )

        if isinstance(e, commands.CommandOnCooldown):
            await self.handle_cooldown(ctx, e.retry_after, False)
        elif isinstance(e, CommandOnKarenCooldown):
            await self.handle_cooldown(ctx, e.remaining, True)
        elif isinstance(e, commands.NoPrivateMessage):
            await ctx.reply_embed(ctx.l.misc.errors.private, ignore_exceptions=True)
        elif isinstance(e, commands.MissingPermissions):
            await ctx.reply_embed(ctx.l.misc.errors.user_perms, ignore_exceptions=True)
        elif isinstance(e, (commands.BotMissingPermissions, discord.errors.Forbidden)):
            await ctx.reply_embed(ctx.l.misc.errors.bot_perms, ignore_exceptions=True)
        elif getattr(e, "original", None) is not None and isinstance(e.original, discord.errors.Forbidden):
            await ctx.reply_embed(ctx.l.misc.errors.bot_perms, ignore_exceptions=True)
        elif isinstance(e, (commands.MaxConcurrencyReached, MaxKarenConcurrencyReached)):
            await ctx.reply_embed(ctx.l.misc.errors.nrn_buddy, ignore_exceptions=True)
        elif isinstance(e, commands.MissingRequiredArgument):
            await ctx.reply_embed(ctx.l.misc.errors.missing_arg, ignore_exceptions=True)
        elif isinstance(e, BAD_ARG_ERRORS):
            await ctx.reply_embed(ctx.l.misc.errors.bad_arg, ignore_exceptions=True)
        elif hasattr(ctx, "failure_reason") and ctx.failure_reason:  # handle global check failures
            failure_reason = ctx.failure_reason

            if failure_reason == "bot_banned" or failure_reason == "ignore":
                return
            elif failure_reason == "not_ready":
                await self.bot.wait_until_ready()
                await ctx.reply_embed(ctx.l.misc.errors.not_ready, ignore_exceptions=True)
            elif failure_reason == "econ_paused":
                await ctx.reply_embed(ctx.l.misc.errors.nrn_buddy, ignore_exceptions=True)
            elif failure_reason == "disabled":
                await ctx.reply_embed(ctx.l.misc.errors.disabled, ignore_exceptions=True)
        elif isinstance(e, IGNORED_ERRORS) or isinstance(getattr(e, "original", None), IGNORED_ERRORS):
            return
        else:  # no error was caught so log error in error channel
            await self.bot.wait_until_ready()
            await ctx.reply_embed(ctx.l.misc.errors.andioop.format(self.d.support), ignore_exceptions=True)

            debug_info = (
                f"```\n{ctx.author} {ctx.author.id} (lang={ctx.l.lang}): {ctx.message.content}"[:200]
                + "```"
                + f"```py\n{format_exception(e).replace('```', '｀｀｀')}"[: 2000 - 206]
                + "```"
            )

            await self.bot.after_ready_ready.wait()
            await self.bot.error_channel.send(debug_info)


def setup(bot):
    bot.add_cog(Events(bot))
