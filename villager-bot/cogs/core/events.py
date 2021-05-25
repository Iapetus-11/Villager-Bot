from discord.ext import commands
import discord
import time
import sys

from util.cooldowns import CommandOnKarenCooldown
from util.code import format_exception


IGNORED_ERRORS = {commands.CommandNotFound, commands.NotOwner}
BAD_ARG_ERRORS = (
    commands.BadArgument,
    commands.errors.UnexpectedQuoteError,
    commands.errors.ExpectedClosingQuoteError,
    commands.errors.BadUnionArgument,
)


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = bot.logger
        self.ipc = bot.ipc

    @commands.Cog.listener()
    async def on_shard_ready(self, shard_id: int):
        await self.ipc.send({"type": "shard-ready", "shard_id": shard_id})
        self.bot.logger.info(f"Shard {shard_id} \u001b[36;1mREADY\u001b[0m")

        # packet = await self.bot.ipc.request({"type": "eval", "code": "v.start_time"})
        # self.bot.logger.info(f"Shard {shard_id} received response {packet}")

    @commands.Cog.listener()
    async def on_shard_disconnect(self, shard_id: int):
        await self.bot.ipc.send({"type": "shard-disconnect", "shard_id": shard_id})

    async def handle_cooldown(self, ctx, remaining: float, karen_cooldown: bool) -> None:
        if ctx.command.name == "mine":
            if await self.db.fetch_item(ctx.author.id, "Efficiency I Book") is not None:
                remaining -= 0.5

            if "haste ii potion" in self.v.chuggers.get(ctx.author.id, []):
                remaining -= 1
            elif "haste i potion" in self.v.chuggers.get(ctx.author.id, []):
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

        await self.bot.send(ctx, random.choice(ctx.l.misc.cooldown_msgs).format(time))

    @commands.Cog.listener()
    async def on_command_error(self, ctx, e: Exception):
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
        elif e in IGNORED_ERRORS or getattr(e, "original", None) in IGNORED_ERRORS:
            return
        else:  # no error was caught so log error in error channel
            debug_info = (
                f"`{ctx.author}` `{ctx.author.id}` (lang={ctx.l.lang}): ```\n{ctx.message.content[:100]}```"
                "```py\n{format_exception(e)}"[: 2000 - 3] + "```"
            )

            await self.bot.get_channel(self.d.error_channel_id).send(debug_info)

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        exception = sys.exc_info()[1]
        traceback = format_exception(exception)

        event_call_repr = f"{event}({', '.join(args + [f"{k}={repr(v)}" for k, v in kwargs.items()])})"
        self.logger.error(f"An exception occurred in this call:\n{event_call_repr}\n\n{traceback}")

        await self.bot.get_channel(self.d.error_channel_id).send(f"```py\n{event_call_repr[:100]}`````py\n{traceback[:1881]}```")


def setup(bot):
    bot.add_cog(Events(bot))
