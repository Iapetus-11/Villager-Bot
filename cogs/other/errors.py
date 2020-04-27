from discord.ext import commands
import discord
from random import choice
import traceback


class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send(self, ctx, msg):
        try:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=msg))
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_command_error(self, ctx, e):
        try:
            if ctx.handled is None:
                ctx.handled = False
        except AttributeError:
            ctx.handled = False

        if isinstance(e, commands.errors.NoPrivateMessage):
            await self.send(ctx, "This command can't be used in private chat channels.")
            return

        if isinstance(e, commands.MissingPermissions) :
            await self.send(ctx, "Nice try stupid, but you don't have the permissions to do that.")
            return

        if isinstance(e, commands.CheckAnyFailure):
            for error in e.errors:
                if isinstance(error, commands.MissingPermissions):
                    await self.send(ctx, "Nice try stupid, but you don't have the permissions to do that.")
                    return

        if isinstance(e, commands.BotMissingPermissions):
            await self.send(ctx, "You didn't give me proper the permissions to do that, stupid.")
            return

        # Commands to ignore
        for _type in [commands.CommandNotFound, commands.NotOwner, commands.CheckFailure, discord.errors.Forbidden]:
            if isinstance(e, _type):
                return

        if isinstance(e, commands.CommandOnCooldown):
            if not str(ctx.command) == "mine" and not str(ctx.command) == "fish":
                descs = ["Didn't your parents tell you patience was a virtue? Calm down and wait another {0} seconds.",
                        "Hey, you need to wait another {0} seconds before doing that again.",
                        "Hrmmm, looks like you need to wait another {0} seconds before doing that again.",
                        "Didn't you know patience was a virtue? Wait another {0} seconds."]
                await self.send(ctx, choice(descs).format(round(e.retry_after, 2)))
            return
        else:
            ctx.command.reset_cooldown(ctx)

        if isinstance(e, commands.errors.MissingRequiredArgument):
            await self.send(ctx, "HRMMM, looks like you're forgetting to put something in!")
            return

        if isinstance(e, commands.BadArgument):
            await self.send(ctx, "Looks like you typed something wrong, try typing it correctly the first time, idiot.")
            return

        if "error code: 50013" in str(e):
            await self.send(ctx, "I can't do that, you idiot.")
            return

        if not "HTTPException: 503 Service Unavailable (error code: 0)" in str(e):
            excls = ['OH SNAP', 'OH FU\*\*!', 'OH \*\*\*\*!', 'OH SH-']
            await self.send(ctx, f"{choice(excls)} "
                                 "You found an actual error, please take a screenshot and report it on our "\
                                 "**[support server](https://discord.gg/39DwwUV)**, thank you!")

        error_channel = self.bot.get_channel(642446655022432267)
        
        # Thanks TrustedMercury!
        etype = type(e)
        trace = e.__traceback__
        verbosity = 1
        lines = traceback.format_exception(etype, e, trace, verbosity)
        traceback_text = ''.join(lines)
        
        await error_channel.send(embed=discord.Embed(color=discord.Color.green(), description=f"```{ctx.author}: {ctx.message.content}\n\n{traceback_text}```"))


def setup(bot):
    bot.add_cog(Errors(bot))
