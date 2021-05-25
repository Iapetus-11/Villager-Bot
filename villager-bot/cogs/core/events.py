from discord.ext import commands
import discord
import time

from util.cooldowns import CommandOnCooldown2
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

    @commands.Cog.listener()
    async def on_shard_ready(self, shard_id: int):
        await self.bot.ipc.send({"type": "shard-ready", "shard_id": shard_id})
        self.bot.logger.info(f"Shard {shard_id} \u001b[36;1mREADY\u001b[0m")

        # packet = await self.bot.ipc.request({"type": "eval", "code": "v.start_time"})
        # self.bot.logger.info(f"Shard {shard_id} received response {packet}")

    @commands.Cog.listener()
    async def on_shard_disconnect(self, shard_id: int):
        await self.bot.ipc.send({"type": "shard-disconnect", "shard_id": shard_id})

    async def handle_cooldown(self, ctx, remaining: float) -> None:
        pass

    @commands.Cog.listener()
    async def on_command_error(self, ctx, e: Exception):
        if e in IGNORED_ERRORS:
            return

        if hasattr(ctx, "custom_error"):
            e = ctx.custom_error

        if isinstance(e, commands.CommandOnCooldown):
            await self.handle_cooldown(ctx, e.retry_after)
        elif isinstance(e, CommandOnCooldown2):
            await self.handle_cooldown(ctx, e.remaining)
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
        else:  # no error was caught so log error in error channel
            debug_info = (
                f"`{ctx.author}` `{ctx.author.id}` (lang={ctx.l.lang}): ```\n{ctx.message.content[:100]}```"
                "```py\n{format_exception(e)}"[: 2000 - 3] + "```"
            )

            await self.bot.get_channel(self.d.error_channel_id).send(debug_info)


def setup(bot):
    bot.add_cog(Events(bot))
