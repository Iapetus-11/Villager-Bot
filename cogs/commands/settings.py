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
            embed.set_author(name="Villager Bot Settings", url=discord.Embed.Empty, icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
            embed.add_field(name="__**General Settings**__", value="""
**{0}config setprefix** ***prefix*** *sets the command prefix in this server*
""".format(ctx.prefix))
            await ctx.send(embed=embed)
        
    @config.command(name="setprefix")
    async def setPrefix(self, ctx, prefix: str):
        for car in prefix:
            if car.lower() not in self.g.allowedChars:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Your new prefix includes an invalid character: \uFEFF ``\uFEFF{0}\uFEFF``".format(car)))
                return
        await self.db.setPrefix(ctx.guild.id, prefix[:16])
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Changed the prefix from ``{0}`` to ``{1}``.".format(ctx.prefix, prefix[:16])))
    
def setup(bot):
    bot.add_cog(Settings(bot))