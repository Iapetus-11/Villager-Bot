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
        stripped = ctx.message.content.replace(f'{ctx.prefix}help', '')

        if len(stripped) > 0:
            if stripped in [cmd.name for cmd in self.bot.commands]:
                # this is for individual help commands
                return

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

    @help.command(name='economy', aliases=['econ'])
    async def help_economy(self, ctx):
        embed = discord.Embed(color=self.d.cc)

        embed.set_author(name='Villager Bot Commands [Economy]', icon_url=self.d.splash_logo)
        embed.set_footer(text='Made by Iapetus11#6821')

        p = ctx.prefix

        embed.description = f'`{p}profile [optional: user]` *shows the profile of you or the specified user*\n\n' \
                            f'`{p}balance [optional: user]` *shows the balance of you or the specified user*\n\n' \
                            f'`{p}inventory [optional: user]` *shows the inventory of you or the specified user*\n\n' \
                            f'`{p}deposit <emerald blocks>` *deposit emeralds into the vault*\n\n' \
                            f'`{p}withdraw <emerald blocks>` *withdraw emeralds from the vault*\n\n' \
                            f'`{p}give <user> <amount> <item>` *give another user an item or emeralds*\n\n' \
                            f'`{p}mine` *mine for emeralds*\n\n' \
                            f'`{p}beg` *beg for emeralds*\n\n' \
                            f'`{p}honey` *harvest honey from the bees you own*\n\n' \
                            f'`{p}gamble <emeralds>` *gamble with the bot for a chance of winning emeralds*\n\n' \
                            f'`{p}pillage <user>` *pillage emeralds from another user*\n\n' \
                            f'`{p}chug <potion>` *use the specified potion*\n\n' \
                            f'`{p}shop` *shows the Villager Shop*\n\n' \
                            f'`{p}buy [optional: amount of item] <item>` *buy an item from the Villager Shop*\n\n' \
                            f'`{p}sell <amount> <item>` *sell items back to Villager Bot*\n\n' \
                            f'`{p}leaderboards` *shows the leaderboards*\n\n'

        await ctx.send(embed=embed)


    @help.command(name='minecraft', aliases=['mc'])
    async def help_minecraft(self, ctx):
        embed = discord.Embed(color=self.d.cc)

        embed.set_author(name='Villager Bot Commands [Minecraft]', icon_url=self.d.splash_logo)
        embed.set_footer(text='Made by Iapetus11#6821')

        p = ctx.prefix

        embed.description = f'`{p}mcstatus [optional: server]` *checks the status of any type of Minecraft server*\n\n' \
                            f'`{p}randommc` *shows a random Minecraft server if you want a new place to explore*\n\n' \
                            f'`{p}mcimage` *turns whatever image you upload into Minecraft blocks / pixel art*\n\n' \
                            f'`{p}stealskin <username>` *fetches the skin of a Minecraft Java Edition player*\n\n' \
                            f'`{p}buildidea` *sends a random build idea for if you\'re bored and need inspiration*\n\n' \
                            f'`{p}mccolors` *shows the Minecraft colors and how to use them in the ingame chat*\n\n' \
                            f'`{p}nametouuid <username>` *turns a MC Java Edition username into a uuid*\n\n' \
                            f'`{p}uuidtoname <uuid>` *turns a MC Java Edition uuid into a username*\n\n'

        await ctx.send(embed=embed)

    @help.command(name='utility', aliases=['util', 'useful'])
    async def help_utility(self, ctx):
        embed = discord.Embed(color=self.d.cc)

        embed.set_author(name='Villager Bot Commands [Utility]', icon_url=self.d.splash_logo)
        embed.set_footer(text='Made by Iapetus11#6821')

        p = ctx.prefix

        embed.description = f'`{p}help` *view helpful information about Villager Bot*\n\n' \
                            f'`{p}config` *configure / setup the bot to your liking*\n\n' \
                            f'`{p}ping` *shows the latency between Discord and Villager Bot*\n\n' \
                            f'`{p}server` *view information about the current server*\n\n' \
                            f'`{p}links` *view useful links relating to Villager Bot*\n\n' \
                            f'`{p}vote` *earn emeralds from voting for Villager Bot on certain websites*\n\n' \
                            f'`{p}info` *view information about Villager Bot*\n\n' \
                            f'`{p}stats` *shows statistics about Villager Bot*\n\n' \
                            f'`{p}uptime` *view how long the bot has been online*\n\n' \
                            f'`{p}google <search>` *searches on google for your query*\n\n' \
                            f'`{p}youtube <search>` *searches on youtube for your query*\n\n' \
                            f'`{p}image <search>` *searches google images for your query*\n\n'

        await ctx.send(embed=embed)

    @help.command(name='fun')
    async def help_fun(self, ctx):
        embed = discord.Embed(color=self.d.cc)

        embed.set_author(name='Villager Bot Commands [Fun]', icon_url=self.d.splash_logo)
        embed.set_footer(text='Made by Iapetus11#6821')

        p = ctx.prefix

        embed.description = f'`{p}cursed` *sends a random cursed Minecraft image*\n\n' \
                            f'`{p}meme` *sends a random meme from reddit*\n\n' \
                            f'`{p}4chan` *shows a funny screenshot from 4chan*\n\n' \
                            f'`{p}comic` *sends a random comic from r/comics on reddit*\n\n' \
                            f'`{p}say <text>` *makes the bot say the text you put in*\n\n' \
                            f'`{p}enchant <text>` *turns text into the Minecraft enchantment table language*\n\n' \
                            f'`{p}unenchant <text>` *turns the enchantment table language back into text*\n\n' \
                            f'`{p}villagerspeak <text>` *turns text into villager sounds*\n\n' \
                            f'`{p}clap <text>` *:clap: puts :clap: the :clap: emoji :clap: between :clap: text*\n\n' \
                            f'`{p}emojify <text>` \uFEFF *:regional_indicator_t::regional_indicator_u::regional_indicator_r::regional_indicator_n::regional_indicator_s: ﻿ ﻿ ﻿:regional_indicator_t::regional_indicator_e::regional_indicator_x::regional_indicator_t: ﻿ ﻿ ﻿:regional_indicator_i::regional_indicator_n::regional_indicator_t::regional_indicator_o: ﻿ ﻿ ﻿:regional_indicator_e::regional_indicator_m::regional_indicator_o::regional_indicator_j::regional_indicator_i::regional_indicator_s:*\n\n' \
                            f'`{p}sarcastic <text>` *turn text into the spongebob sarcastic text*\n\n' \
                            f'`{p}owo <text>` *owofies the given text uwu*\n\n' \
                            f'`{p}vaporwave <text>` *makes text into the vaporwave style*\n\n' \
                            f'`{p}kill <user>` *fake kill another user*\n\n' \
                            f'`{p}bubblewrap` *sends virtual bubblewrap for you to pop*\n\n' \
                            f'`{p}coinflip` *flips a coin and says the result in the chat*\n\n'

        await ctx.send(embed=embed)


    @help.command(name='administrator', aliases=['mod', 'moderation', 'administrative', 'admin'])
    async def help_administrative(self, ctx):
        embed = discord.Embed(color=self.d.cc)

        embed.set_author(name='Villager Bot Commands [Admin]', icon_url=self.d.splash_logo)
        embed.set_footer(text='Made by Iapetus11#6821')

        p = ctx.prefix

        embed.description = f'`{p}warn <user> <reason>` *warn a user for a specified reason*\n\n' \
                            f'`{p}warns <user>` *view the warns a user has, leave blank to see your warnings*\n\n' \
                            f'`{p}purge [optional: user] <amount>` *purge messages from the current channel*\n\n' \
                            f'`{p}delwarns <user>` *clears the warns that user has in this server*\n\n' \
                            f'`{p}kick <user>` *kicks the user from the current Discord server*\n\n' \
                            f'`{p}ban <user>` *bans the user from the current Discord server*\n\n' \
                            f'`{p}pardon <user>` *unban the user from the current Discord server*\n\n' \

        await ctx.send(embed=embed)

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

        if (days := diff.days) == 1:
            dd = ctx.l.useful.uptime.day
        else:
            dd = ctx.l.useful.uptime.days

        if (hours := int(diff.seconds / 3600)) == 1:
            hh = ctx.l.useful.uptime.hour
        else:
            hh = ctx.l.useful.uptime.hours

        if (minutes := int(diff.seconds / 60) % 60) == 1:
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

        embed.add_field(name=ctx.l.useful.info.more, value=f'{ctx.l.useful.info.click_here}]({self.d.topgg})')
        embed.add_field(name=ctx.l.useful.info.website, value=f'[{ctx.l.useful.info.click_here}]({self.d.website})')
        embed.add_field(name=ctx.l.useful.info.support, value=f'[{ctx.l.useful.info.click_here}]({self.d.support})')

        embed.set_author(name=ctx.l.useful.info.title, icon_url=self.d.splash_logo)

        await ctx.send(embed=embed)

    @commands.command(name='vote', aliases=['votelink', 'votelinks'])
    async def votelinks(self, ctx):
        embed = discord.Embed(color=self.d.cc)
        embed.set_author(name='Vote for Villager Bot!', icon_url=self.d.splash_logo)

        embed.description = f'**[{ctx.l.useful.vote.click_1}]({self.d.topgg})**'

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
        uptime = (arrow.utcnow() - self.d.start_time)
        uptime_seconds = uptime.seconds + (uptime.days * 24 * 3600)

        proc =  psutil.Process()
        mem_usage = proc.memory_full_info().uss
        proc.cpu_percent(interval=.75)

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
                  f'{ctx.l.useful.ginf.emojis}: `{len(guild.emojis)}`\n'

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

    @commands.command(name='google', aliases=['search', 'thegoogle'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def google_search(self, ctx, *, query):
        try:
            with ctx.typing():
                res = await self.google_client.search(query, safesearch=ctx.channel.is_nsfw())
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
        try:
            with ctx.typing():
                res = await self.google_client.search(query, safesearch=ctx.channel.is_nsfw())
        except async_cse.search.NoResults:
            await self.bot.send(ctx, ctx.l.useful.search.nope)
            return
        except async_cse.search.APIError:
            await self.bot.send(ctx, ctx.l.useful.search.error)
            return

        res = (*filter((lambda r: 'youtube' in r.url), res),)

        if len(res) == 0:
            await self.bot.send(ctx, ctx.l.useful.search.nope)
            return

        res = res[0]

        await ctx.send(res.url)

    @commands.command(name='image', aliases=['imagesearch', 'img'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def image_search(self, ctx, *, query):
        try:
            with ctx.typing():
                res = await self.google_client.search(query, safesearch=ctx.channel.is_nsfw(), image_search=True)
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
