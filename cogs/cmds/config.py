from discord.ext import commands
import discord


class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = self.bot.d

        self.db = self.bot.db

    @commands.group(name='config', aliases=['settings', 'conf'])
    async def config(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(color=self.d.cc)

            guild_conf = 'bruh'
            embed.add_field(name='Server/Guild Configuration', value=guild_conf)

            user_conf = 'bruh2.0'
            embed.add_field(name='Per User Configuration', value=user_conf)

            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Config(bot))
