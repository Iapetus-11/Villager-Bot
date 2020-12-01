from discord.ext import commands
import util.math
import async_cse
import discord
import psutil
import arrow


class Useful(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.d = self.bot.d

        self.google_client = async_cse.Search(self.d.google_keys)

        self.db = self.bot.get_cog('Database')

    @commands.group(name='help')
    async def help(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(color=self.d.cc)
            embed.set_author(name=ctx.l.help.n.title, icon_url=self.d.splash_logo)
            embed.description = ctx.l.help.main.desc.format(self.d.support, self.d.topgg)

            p = ctx.prefix

            embed.add_field(name=ctx.l.help.n.economy, value=f'`{p}help econ`')
            embed.add_field(name=ctx.l.help.n.minecraft, value=f'`{p}help mc`')
            embed.add_field(name=ctx.l.help.n.utility, value=f'`{p}help util`')

            embed.add_field(name=ctx.l.help.n.fun, value=f'`{p}help fun`')
            embed.add_field(name=ctx.l.help.n.admin, value=f'`{p}help admin`')
            embed.add_field(name=ctx.l.help.main.support, value=f'[**{ctx.l.help.main.clickme}**]({self.d.support})')

            await ctx.send(embed=embed)

    @help.command(name='economy', aliases=['econ'])
    async def help_economy(self, ctx):
        embed = discord.Embed(color=self.d.cc)

        embed.set_author(name=f'{ctx.l.help.n.title} [{ctx.l.help.n.economy}]', icon_url=self.d.splash_logo)
        embed.set_footer(text=ctx.l.misc.petus)

        embed.description = ''.join(ctx.l.help.econ).format(ctx.prefix)

        await ctx.send(embed=embed)

    @help.command(name='minecraft', aliases=['mc'])
    async def help_minecraft(self, ctx):
        embed = discord.Embed(color=self.d.cc)

        embed.set_author(name=f'{ctx.l.help.n.title} [{ctx.l.help.n.minecraft}]', icon_url=self.d.splash_logo)
        embed.set_footer(text=ctx.l.misc.petus)

        embed.description = ''.join(ctx.l.help.mc).format(ctx.prefix)

        await ctx.send(embed=embed)

    @help.command(name='utility', aliases=['util', 'useful'])
    async def help_utility(self, ctx):
        embed = discord.Embed(color=self.d.cc)

        embed.set_author(name=f'{ctx.l.help.n.title} [{ctx.l.help.n.utility}]', icon_url=self.d.splash_logo)
        embed.set_footer(text=ctx.l.misc.petus)

        p = ctx.prefix

        embed.description = ''.join(ctx.l.help.util).format(ctx.prefix)

        await ctx.send(embed=embed)

    @help.command(name='fun')
    async def help_fun(self, ctx):
        embed = discord.Embed(color=self.d.cc)

        embed.set_author(name=f'{ctx.l.help.n.title} [{ctx.l.help.n.fun}]', icon_url=self.d.splash_logo)
        embed.set_footer(text=ctx.l.misc.petus)

        p = ctx.prefix

        embed.description = ''.join(ctx.l.help.fun).format(ctx.prefix)

        await ctx.send(embed=embed)

    @help.command(name='administrator', aliases=['mod', 'moderation', 'administrative', 'admin'])
    async def help_administrative(self, ctx):
        embed = discord.Embed(color=self.d.cc)

        embed.set_author(name=f'{ctx.l.help.n.title} [{ctx.l.help.n.admin}]', icon_url=self.d.splash_logo)
        embed.set_footer(text=ctx.l.misc.petus)

        p = ctx.prefix

        embed.description = ''.join(ctx.l.help.mod).format(ctx.prefix)

        await ctx.send(embed=embed)

    @commands.command(name='aliases')
    async def show_aliases(self, ctx, command):
        command = command.lower()
        all_cmds = [[str(c), *[str(a) for a in c.aliases]] for c in self.bot.commands]

        for alias_group in all_cmds:
            if command in alias_group:
                if len(alias_group) > 1:
                    alias_group.pop(alias_group.index(command))
                    await self.bot.send(ctx, ctx.l.useful.aliases.aliases.format(command, '`, `'.join(alias_group)))
                    return

        await self.bot.send(ctx, ctx.l.useful.aliases.none.format(command))

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
            await self.bot.send(ctx, f'{self.d.emojis.aniheart} Magnum Dong! \uFEFF `69.00 ms`')
            return

        await self.bot.send(ctx, f'{self.d.emojis.aniheart} {pp} \uFEFF `{round(self.bot.latency*1000, 2)} ms`')

    @commands.command(name='uptime', aliases=['isvillagerbotdown', 'isthebestbotintheworldoffline'])
    async def uptime(self, ctx):
        now = arrow.utcnow()
        diff = now - self.d.start_time

        days = diff.days
        if days == 1:
            dd = ctx.l.useful.uptime.day
        else:
            dd = ctx.l.useful.uptime.days

        hours = int(diff.seconds / 3600)
        if hours == 1:
            hh = ctx.l.useful.uptime.hour
        else:
            hh = ctx.l.useful.uptime.hours

        minutes = int(diff.seconds / 60) % 60
        if minutes == 1:
            mm = ctx.l.useful.uptime.minute
        else:
            mm = ctx.l.useful.uptime.minutes

        await self.bot.send(ctx, ctx.l.useful.uptime.online_for.format(f'{days} {dd}, {hours} {hh}, {minutes} {mm}'))

    @commands.command(name='info', aliases=['information'])
    async def info(self, ctx):
        embed = discord.Embed(color=self.d.cc)

        embed.add_field(name=ctx.l.useful.info.lib, value='Discord.py')
        embed.add_field(name=ctx.l.useful.info.prefix, value=ctx.prefix)
        embed.add_field(name=ctx.l.useful.info.creator, value='Iapetus11#6821')

        embed.add_field(name=ctx.l.useful.info.servers, value=str(len(self.bot.guilds)))
        embed.add_field(name=ctx.l.useful.info.shards, value=str(self.bot.shard_count))
        embed.add_field(name=ctx.l.useful.info.users, value=str(len(self.bot.users)))

        embed.add_field(name=ctx.l.useful.info.more, value=f'[{ctx.l.useful.info.click_here}]({self.d.topgg})')
        embed.add_field(name=ctx.l.useful.info.website, value=f'[{ctx.l.useful.info.click_here}]({self.d.website})')
        embed.add_field(name=ctx.l.useful.info.support, value=f'[{ctx.l.useful.info.click_here}]({self.d.support})')

        embed.set_author(name=ctx.l.useful.info.title, icon_url=self.d.splash_logo)

        await ctx.send(embed=embed)

    @commands.command(name='vote', aliases=['votelink', 'votelinks'])
    async def votelinks(self, ctx):
        embed = discord.Embed(color=self.d.cc)
        embed.set_author(name='Vote for Villager Bot!', icon_url=self.d.splash_logo)

        embed.description = f'**[{ctx.l.useful.vote.click_1}]({self.d.topgg + "/vote"})**'

        await ctx.send(embed=embed)

    @commands.command(name='links', aliases=['invite', 'support', 'usefullinks', 'website'])
    async def useful_links(self, ctx):
        embed = discord.Embed(color=self.d.cc)
        embed.set_author(name='Useful Links', icon_url=self.d.splash_logo)

        embed.description = f'**[{ctx.l.useful.links.support}]({self.d.support})\n' \
                            f'\n[{ctx.l.useful.links.invite}]({self.d.invite})\n' \
                            f'\n[{ctx.l.useful.links.topgg}]({self.d.topgg})\n' \
                            f'\n[{ctx.l.useful.links.website}]({self.d.website})\n' \
                            f'\n[{ctx.l.useful.links.source}]({self.d.github})**'

        await ctx.send(embed=embed)

    @commands.command(name='stats', aliases=['bs'])
    async def stats(self, ctx):
        with ctx.typing():
            uptime = (arrow.utcnow() - self.d.start_time)
            uptime_seconds = uptime.seconds + (uptime.days * 24 * 3600)

            proc =  psutil.Process()
            with proc.oneshot():
                mem_usage = proc.memory_full_info().uss
                threads = proc.num_threads()
                proc.cpu_percent(interval=.1)

            embed = discord.Embed(color=self.d.cc)

            embed.set_author(name='Villager Bot Statistics', icon_url=self.d.splash_logo)
            embed.set_footer(text='Made by Iapetus11#6821')

            col_1 = f'{ctx.l.useful.stats.servers}: `{len(self.bot.guilds)}`\n' \
                    f'{ctx.l.useful.stats.dms}: `{len(self.bot.private_channels)}/128`\n' \
                    f'{ctx.l.useful.stats.users}: `{len(self.bot.users)}`\n' \
                    f'{ctx.l.useful.stats.msgs}: `{self.d.msg_count}`\n' \
                    f'{ctx.l.useful.stats.cmds}: `{self.d.cmd_count}` `({round((self.d.cmd_count / (self.d.msg_count + .000001)) * 100, 2)}%)`\n' \
                    f'{ctx.l.useful.stats.cmds_sec}: `{round(self.d.cmd_count / uptime_seconds, 2)}`\n' \
                    f'{ctx.l.useful.stats.votes}: `{self.d.votes_topgg}`\n' \
                    f'{ctx.l.useful.stats.topgg}: `{round((self.d.votes_topgg / uptime_seconds) * 3600, 2)}`\n'

            col_2 = f'{ctx.l.useful.stats.mem}: `{round(mem_usage / 1000000, 2)} MB`\n' \
                    f'{ctx.l.useful.stats.cpu}: `{round(proc.cpu_percent() / psutil.cpu_count(), 2)}%`\n' \
                    f'{ctx.l.useful.stats.threads}: `{threads}`\n' \
                    f'{ctx.l.useful.stats.ping}: `{round(self.bot.latency * 1000, 2)} ms`\n' \
                    f'{ctx.l.useful.stats.shards}: `{self.bot.shard_count}`\n' \
                    f'{ctx.l.useful.stats.uptime}: `{uptime_seconds}s`\n'

            embed.add_field(name='\uFEFF', value=col_1+'\uFEFF')
            embed.add_field(name='\uFEFF', value=col_2+'\uFEFF')

        await ctx.send(embed=embed)

    @commands.command(name='guildinfo', aliases=['server', 'serverinfo', 'guild'])
    @commands.guild_only()
    async def guild_info(self, ctx, gid: int = None):
        if gid is None:
            guild = ctx.guild
        else:
            guild = self.bot.get_guild(gid)

        db_guild = await self.db.fetch_guild(guild.id)

        embed = discord.Embed(color=self.d.cc)
        embed.set_author(name=f'{guild.name} {ctx.l.useful.ginf.info}', icon_url=guild.icon_url)

        general = f'{ctx.l.useful.ginf.owner}: {guild.owner.mention}\n' \
                  f'{ctx.l.useful.ginf.members}: `{guild.member_count}`\n' \
                  f'{ctx.l.useful.ginf.channels}: `{len(guild.channels)}`\n ' \
                  f'{ctx.l.useful.ginf.roles}: `{len(guild.roles)}`\n' \
                  f'{ctx.l.useful.ginf.emojis}: `{len(guild.emojis)}`\n' \
                  f'{ctx.l.useful.ginf.bans}: `{len(await guild.bans())}`\n'

        villager = f'{ctx.l.useful.ginf.cmd_prefix}: `{self.d.prefix_cache.get(guild.id, self.d.default_prefix)}`\n' \
                   f'{ctx.l.useful.ginf.lang}: `{ctx.l.name}`\n' \
                   f'{ctx.l.useful.ginf.diff}: `{db_guild["difficulty"]}`\n'

        embed.add_field(name='General', value=general, inline=False)
        embed.add_field(name='Villager Bot', value=villager, inline=False)

        embed.set_thumbnail(url=guild.icon_url)

        await ctx.send(embed=embed)

    @commands.command(name='math', aliases=['solve', 'meth'])
    async def math(self, ctx, *, problem):
        try:
            await self.bot.send(ctx, f'```{util.math.parse(problem)}```')
        except Exception:
            await self.bot.send(ctx, ctx.l.useful.meth.oops)

    @commands.command(name='google', aliases=['thegoogle'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def google_search(self, ctx, *, query):
        safesearch = True
        if isinstance(ctx.channel, discord.TextChannel):
            safesearch = not ctx.channel.is_nsfw()

        try:
            with ctx.typing():
                res = await self.google_client.search(query, safesearch=safesearch)
        except async_cse.search.NoResults:
            await self.bot.send(ctx, ctx.l.useful.search.nope)
            return
        except async_cse.search.APIError:
            await self.bot.send(ctx, ctx.l.useful.search.error)
            return

        if len(res) == 0:
            await self.bot.send(ctx, ctx.l.useful.search.nope)
            return

        res = res[0]

        embed = discord.Embed(color=self.d.cc, title=res.title, description=res.description, url=res.url)
        await ctx.send(embed=embed)

    @commands.command(name='youtube', aliases=['ytsearch', 'yt'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def youtube_search(self, ctx, *, query):
        safesearch = True
        if isinstance(ctx.channel, discord.TextChannel):
            safesearch = not ctx.channel.is_nsfw()

        try:
            with ctx.typing():
                res = await self.google_client.search(query, safesearch=safesearch)
        except async_cse.search.NoResults:
            await self.bot.send(ctx, ctx.l.useful.search.nope)
            return
        except async_cse.search.APIError:
            await self.bot.send(ctx, ctx.l.useful.search.error)
            return

        res = (*filter((lambda r: 'youtube.com/watch' in r.url), res),)

        if len(res) == 0:
            await self.bot.send(ctx, ctx.l.useful.search.nope)
            return

        res = res[0]

        await ctx.send(res.url)

    @commands.command(name='image', aliases=['imagesearch', 'img'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def image_search(self, ctx, *, query):
        safesearch = True
        if isinstance(ctx.channel, discord.TextChannel):
            safesearch = not ctx.channel.is_nsfw()

        try:
            with ctx.typing():
                res = await self.google_client.search(query, safesearch=safesearch, image_search=True)
        except async_cse.search.NoResults:
            await self.bot.send(ctx, ctx.l.useful.search.nope)
            return
        except async_cse.search.APIError:
            await self.bot.send(ctx, ctx.l.useful.search.error)
            return

        if len(res) == 0:
            await self.bot.send(ctx, ctx.l.useful.search.nope)
            return

        res = res[0]

        await ctx.send(res.image_url)


def setup(bot):
    bot.add_cog(Useful(bot))
