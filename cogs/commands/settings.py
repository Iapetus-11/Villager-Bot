from discord.ext import commands
import discord


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.g = self.bot.get_cog("Global")
        self.db = self.bot.get_cog("Database")

    @commands.group(name="config", aliases=["conf", "cfg"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def config(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(color=discord.Color.green(), description="")
            embed.set_author(name="Villager Bot Settings", url=discord.Embed.Empty, icon_url="http://olimone.ddns.net/images/villagerbotsplash1.png")
            embed.add_field(name="__**General Settings**__", value="""
**{0}config prefix** ***prefix*** *sets the command prefix in this server to the specified value*
**{0}config replies** ***on/off*** *turn bot replies to messages (like the bot would say "hrmm" to "emeralds") on/off in this server*
**{0}config tips** ***on/off*** *turn on/off message tips in this server*
""".format(ctx.prefix))
            await ctx.send(embed=embed)

    @config.command(name="prefix")
    async def set_prefix(self, ctx, prefix=None):
        if prefix is None:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"The current prefix is ``{await self.db.get_prefix(ctx.guild.id)}``"))
            return
        for car in prefix:
            if car.lower() not in self.g.allowedChars:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Your new prefix includes an invalid character: \uFEFF ``\uFEFF{0}\uFEFF``".format(car)))
                return
        await self.db.set_prefix(ctx.guild.id, prefix[:16])
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Changed the prefix from ``{0}`` to ``{1}``.".format(ctx.prefix, prefix[:16])))

    @config.command(name="replies")
    async def set_do_replies(self, ctx, doem=None):
        if doem is None:
            if await self.db.get_do_replies(ctx.guild.id):
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Message replies are currently **enabled**."))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Message replies are currently **disabled**."))
            return
        doem = doem.lower()
        if doem == "on" or doem == "true":
            await self.db.set_do_replies(ctx.guild.id, True)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="**Enabled** message replies."))
        elif doem == "off" or doem == "false":
            await self.db.set_do_replies(ctx.guild.id, False)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="**Disabled** message replies."))
        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That is not a valid option! Only ``on`` and ``off`` are valid options."))

    @config.command(name="tips")
    async def set_do_tips(self, ctx, doem=None):
        if doem is None:
            if await self.db.get_do_tips(ctx.guild.id):
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Tips are currently **enabled**."))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Tips are currently **disabled**."))
            return
        doem = doem.lower()
        if doem == "on" or doem == "true":
            await self.db.set_do_tips(ctx.guild.id, True)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="**Enabled** tips."))
        elif doem == "off" or doem == "false":
            await self.db.set_do_tips(ctx.guild.id, False)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="**Disabled** tips."))
        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That is not a valid option! Only ``on`` and ``off`` are valid options."))

def setup(bot):
    bot.add_cog(Settings(bot))
