from discord.ext import commands
import discord
import arrow


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
        elif 'shing' in content or 'shling' in content:
            pp = 'Schlong'
        elif 'schlong' in content:
            print(1)
            await self.bot.send(ctx, f'{self.d.emojis.aniheart} Magnum Dong! \uFEFF `69.00 ms`')
            return

        await self.bot.send(ctx, f'{self.d.emojis.aniheart} {pp} \uFEFF `{round(self.bot.latency*1000, 2)} ms`')

    @commands.command(name='uptime', aliases=['isvillagerbotdown'])
    async def uptime(self, ctx):
        now = arrow.utcnow()
        diff = now - self.d.start_time

        if days := diff.days == 1:
            dd = 'day'
        else:
            dd = 'days'

        if hours := int(diff.seconds / 3600) == 1:
            hh = 'hour'
        else:
            hh = 'hours'

        if minutes := int(diff.seconds / 60) % 60 == 1:
            mm = 'minute'
        else:
            mm = 'minutes'

        await self.bot.send(ctx, f'Bot has been online for {days} {dd}, {hours} {hh}, {minutes} {mm}.')

    @commands.command(name='stats', aliases=['bs'])
    async def stats(self, ctx):
        uptime = (arrow.utcnow() - self.d.start_time)
        uptime_seconds = uptime.seconds + (uptime.days * 24 * 3600)

        body = f'Server Count: `{len(self.bot.guilds)}`' \
               f'DM Channel Count: `{len(self.bot.private_channels)}/128`' \
               f'User Count: `{len(self.bot.users)}`' \
               f'Session Message Count: `{self.d.msg_count}`' \
               f'Session Command Count: `{self.d.cmd_count}` `({round((self.d.cmd_count / self.d.msg_count) * 100, 2)}% of all msgs)`' \
               f'Commands/Second: `{round(self.d.cmd_count / uptime_seconds, 2)}`' \
               f'Session Vote Count: `{self.d.votes_disbots + self.d.votes_topgg}`' \
               f'Disbots.gg Votes / Hour: `{round((self.d.votes_disbots / uptime_seconds) * 3600, 2)}`' \
               f'Top.gg Votes / Hour: `{round((self.d.votes_topgg / uptime_seconds) * 3600, 2)}`' \
               f'Shard Count: `{self.bot.shard_count}`' \
               f'Latency/Ping: `{round(self.bot.latency * 1000, 2)} ms`'

        embed = discord.Embed(color=self.d.cc, description=body)
        embed.set_author(name='Villager Bot Statistics', icon_url=self.d.splash_logo)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Useful(bot))
