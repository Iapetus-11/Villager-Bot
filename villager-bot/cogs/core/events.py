from discord.ext import commands
import discord
import random
import time
import sys

from util.cooldowns import CommandOnKarenCooldown
from util.code import format_exception


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

        bot.event(self.on_error)  # discord.py's Cog.listener() doesn't work for on_error events

    async def on_error(self, event, *args, **kwargs):  # logs errors in events, such as on_message
        self.bot.error_count += 1

        exception = sys.exc_info()[1]
        traceback = format_exception(exception)

        event_call_repr = f"{event}({',  '.join(list(map(repr, args)) + [f'{k}={repr(v)}' for k, v in kwargs.items()])})"
        self.logger.error(f"An exception occurred in this call:\n{event_call_repr}\n\n{traceback}")

        error_channel = await self.bot.fetch_error_channel()
        await error_channel.send(f"```py\n{event_call_repr[:100]}``````py\n{traceback[:1880]}```")

    @commands.Cog.listener()
    async def on_shard_ready(self, shard_id: int):
        await self.ipc.send({"type": "shard-ready", "shard_id": shard_id})
        self.bot.logger.info(f"Shard {shard_id} \u001b[36;1mREADY\u001b[0m")

    @commands.Cog.listener()
    async def on_shard_disconnect(self, shard_id: int):
        await self.ipc.send({"type": "shard-disconnect", "shard_id": shard_id})

    @commands.Cog.listener()
    async def on_message(self, message):
        self.bot.message_count += 1

        if message.author.bot:
            return

        if isinstance(message.channel, discord.DMChannel):
            await self.ipc.send({"type": "dm-message", "user": message.author.id, "content": message.content})

        if message.content.startswith(f"<@!{self.bot.user.id}>") or message.content.startswith(f"<@{self.bot.user.id}>"):
            if message.guild is None:
                prefix = self.d.default_prefix
            else:
                prefix = self.bot.prefix_cache.get(message.guild.id, self.d.default_prefix)

            lang = self.bot.get_language(message)

            embed = discord.Embed(color=self.d.cc, description=lang.misc.pingpong.format(prefix, self.d.support))
            embed.set_author(name="Villager Bot", icon_url=self.d.splash_logo)
            embed.set_footer(text=lang.misc.petus)

            await message.channel.send(embed=embed)
            return

        if message.guild is not None:
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
                    await message.channel.send(
                        f"@someone {INVISIBLITY_CLOAK} {random.choice(someones).mention} {message.author.mention}"
                    )
                    return

            if message.guild.id in self.bot.replies_cache:
                prefix = self.bot.prefix_cache.get(message.guild.id, self.d.default_prefix)

                if not message.content.startswith(prefix):
                    if "emerald" in content_lower:
                        await message.channel.send(random.choice(self.d.hmms))
                    elif "creeper" in content_lower:
                        await message.channel.send("awww{} man".format(random.randint(1, 5) * "w"))
                    elif "reee" in content_lower:
                        await message.channel.send(random.choice(self.d.emojis.reees))
                    elif "amogus" in content_lower or content_lower == "sus":
                        await message.channel.send(self.d.emojis.amogus)

    async def handle_cooldown(self, ctx, remaining: float, karen_cooldown: bool) -> None:
        if ctx.command.name == "mine":
            if await self.db.fetch_item(ctx.author.id, "Efficiency I Book") is not None:
                remaining -= 0.5
            
            active_effects = await self.ipc.eval(f"active_effects.get({ctx.author.id})")

            if active_effects:
                if "haste ii potion" in active_effects:
                    remaining -= 1
                elif "haste i potion" in active_effects:
                    remaining -= 0.5

        seconds = round(remaining, 2)

        if seconds <= 0.05:
            if karen_cooldown:
                await self.ipc.send({"type": "cooldown-add", "command": ctx.command.name, "user_id": ctx.author.id})

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

        await self.bot.reply_embed(ctx, random.choice(ctx.l.misc.cooldown_msgs).format(time))

    @commands.Cog.listener()
    async def on_command_error(self, ctx, e: Exception):
        self.bot.error_count += 1

        if hasattr(ctx, "custom_error"):
            e = ctx.custom_error

        if isinstance(e, commands.CommandOnCooldown):
            await self.handle_cooldown(ctx, e.retry_after, False)
        elif isinstance(e, CommandOnKarenCooldown):
            await self.handle_cooldown(ctx, e.remaining, True)
        elif isinstance(e, commands.NoPrivateMessage):
            await self.bot.reply_embed(ctx, ctx.l.misc.errors.private)
        elif isinstance(e, commands.MissingPermissions):
            await self.bot.reply_embed(ctx, ctx.l.misc.errors.user_perms)
        elif isinstance(e, (commands.BotMissingPermissions, discord.errors.Forbidden)):
            await self.bot.reply_embed(ctx, ctx.l.misc.errors.bot_perms)
        elif getattr(e, "original", None) is not None and isinstance(e.original, discord.errors.Forbidden):
            await self.bot.reply_embed(ctx, ctx.l.misc.errors.bot_perms)
        elif isinstance(e, commands.MaxConcurrencyReached):
            await self.bot.reply_embed(ctx, ctx.l.misc.errors.nrn_buddy)
        elif isinstance(e, commands.MissingRequiredArgument):
            await self.bot.reply_embed(ctx, ctx.l.misc.errors.missing_arg)
        elif isinstance(e, BAD_ARG_ERRORS):
            await self.bot.reply_embed(ctx, ctx.l.misc.errors.bad_arg)
        elif hasattr(ctx, "failure_reason") and ctx.failure_reason:  # handle global check failures
            failure_reason = ctx.failure_reason

            if failure_reason == "bot_banned" or failure_reason == "ignore":
                return
            elif failure_reason == "not_ready":
                await self.bot.wait_until_ready()
                await self.bot.reply_embed(ctx, ctx.l.misc.errors.not_ready)
            elif failure_reason == "econ_paused":
                await self.bot.reply_embed(ctx, ctx.l.misc.errors.nrn_buddy)
            elif failure_reason == "disabled":
                await self.bot.reply_embed(ctx, ctx.l.misc.errors.disabled)
        elif isinstance(e, IGNORED_ERRORS) or isinstance(getattr(e, "original", None), IGNORED_ERRORS):
            return
        else:  # no error was caught so log error in error channel
            try:
                await self.bot.reply_embed(ctx, ctx.l.misc.errors.andioop.format(self.d.support))
            except Exception:
                pass

            debug_info = (
                f"`{ctx.author}` `{ctx.author.id}` (lang={ctx.l.lang}): ```\n{ctx.message.content[:100]}```"
                f"```py\n{format_exception(e)}"[: 2000 - 3] + "```"
            )

            error_channel = await self.bot.fetch_error_channel()
            await error_channel.send(debug_info)


def setup(bot):
    bot.add_cog(Events(bot))
