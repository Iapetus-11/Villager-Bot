from discord.ext import commands
import discord
from random import choice


class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if type(error) == discord.ext.commands.CommandNotFound or type(error) == discord.ext.commands.NotOwner or type(error) == discord.ext.commands.errors.CheckFailure: # Errrors to completely ignore
            return

        if type(error) == discord.ext.commands.errors.NoPrivateMessage:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="This command can't be used in private chat channels!"))
            return

        if type(error) == discord.ext.commands.errors.MissingRequiredArgument:
            if str(ctx.command) == "gamble":
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Aren't you forgetting something? Perhaps you need to specify the quantity of emeralds to gamble with..."))
            elif str(ctx.command) == "battle" or str(ctx.command) == "pillage":
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Uh oh, the command didn't work. Maybe you should actually mention a person?"))
            elif str(ctx.command) == "give":
                if str(error.param) == "rec":
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Maybe you should tell me who to send the emeralds to, next time I'm keeping them!"))
                else:
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Look at that, you didn't specify how many emeralds to give, I'll just send them all."))
            elif str(ctx.command) == "kick" or str(ctx.command) == "ban" or str(ctx.command) == "pardon":
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Oh, would you look at that! You didn't tell me who to " + str(ctx.command) + "."))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="HRMMM, looks like you're forgetting to put something in!"))
            return

        elif type(error) == discord.ext.commands.CommandOnCooldown:
            cooldownmsgs = ["Didn't your parents tell you patience was a virtue? Calm down and wait another {0} seconds.", "Hey, you need to wait another {0} seconds before doing that again.",
                            "Hrmmm, looks like you need to wait another {0} seconds before doing that again.", "Didn't you know patience was a virtue? Wait another {0} seconds."]
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(cooldownmsgs).format(round(error.retry_after, 2))))
            return

        elif type(error) == discord.ext.commands.BadArgument:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Looks like you typed something wrong, try typing it correctly the first time, duh."))
            return

        elif type(error) == discord.ext.commands.MissingPermissions:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Nice try stupid, but you don't have the permissions to do that."))
            return

        elif type(error) == discord.ext.commands.BotMissingPermissions:
            try:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You didn't give me the permissions to do that, idiot."))
            except Exception:
                pass
            return

        elif "error code: 50013" in str(error):
            try:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="I can't do that, you idiot."))
            except Exception:
                pass
            return

        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["OH SNAP.", "OH FU\*\*.", "\*\*\*\*\*\*\*\*\*\*."]) +
                                               " You found an actual error, please take a screenshot and report it on our [support server](https://discord.gg/39DwwUV). Thanks!"))

        channel = self.bot.get_channel(642446655022432267)
        await channel.send("```" + str(ctx.author) + ": " + ctx.message.content + "\n\nError: " + str(error) + "\n\nType: " + str(type(error)) + "```")


def setup(bot):
    bot.add_cog(Errors(bot))
