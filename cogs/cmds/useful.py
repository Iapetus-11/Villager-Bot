from discord.ext import commands
import discord


class Useful(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='help')
    async def cmd_help(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed()
            p = ctx.prefix

            embed.add_field(name='Minecraft', value=f'{p}help mc')
            embed.add_field(name='\uFEFF', value='\uFEFF')
            embed.add_field(name='Fun', value=f'{p}help fun')

            embed.add_field(name='\uFEFF', value='\uFEFF')
            embed.add_field(name='Economy', value=f'{p}help econ')
            embed.add_field(name='\uFEFF', value='\uFEFF')

            embed.add_field(name='Useful', value=f'{p}help useful')
            embed.add_field(name='\uFEFF', value='\uFEFF')
            embed.add_field(name='Admin', value=f'{p}help admin')

            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Useful(bot))
