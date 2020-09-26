from discord.ext import commands
import discord


class Useful(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = self.bot.d

    """
    @commands.group(name='help')
    async def help(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(color=self.d.cc)
            embed.set_author(name='Villager Bot Commands', icon_url=self.d.splash_logo)
            embed.description = f'Need more help? Check out the [**Support Server**]({self.d.support})!\n' \
                                f'Enjoying the bot? Vote for us on [**top.gg**]({self.d.topgg}) and earn emeralds!'

            p = ctx.prefix

            embed.add_field(name='Economy', value=f'`{p}help econ`')
            embed.add_field(name='Minecraft', value=f'`{p}help mc`')
            embed.add_field(name='Utility', value=f'`{p}help util`')

            embed.add_field(name='Fun', value=f'`{p}help fun`')
            embed.add_field(name='Admin', value=f'`{p}help admin`')
            embed.add_field(name='Support', value=f'[**Click Me**]({self.d.support})')

            await ctx.send(embed=embed)
    """

    @commands.command(name='ping', aliases=['pong', 'ding', 'dong', 'shing', 'shling', 'schlong'])
    async def ping_pong(self, ctx):
        content = ctx.message.content.lower()

        if 'ping' in content:
            pp = 'Pong'
        elif 'pong' in content:
            pp = 'Ping'
        elif 'ding' in content:
            pp = 'Dong'
        elif 'dong' in content:
            pp = 'Ding'
        elif 'shing' or 'shling' in content:
            pp = 'Schlong'
        elif 'schlong' in content:
            await self.bot.send(ctx, f'{self.d.emojis.aniheart} \uFEFF `69.00 ms`')
            return

        await self.bot.send(ctx, f'{self.d.emojis.aniheart} \uFEFF `{round(self.bot.latency*1000, 2)} ms`')


def setup(bot):
    bot.add_cog(Useful(bot))
