from discord.ext import commands
import traceback
import discord
import logging
import random


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.d = self.bot.d

        self.db = self.bot.get_cog('Database')

        self.logger = logging.getLogger("Events")
        self.logger.setLevel(logging.INFO)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(activity=discord.Game(name=random.choice(self.d.playing_list)))

        self.d.ban_cache = await self.db.fetch_all_botbans()
        self.d.lang_cache = await self.db.fetch_all_guild_langs()
        self.d.prefix_cache = await self.db.fetch_all_guild_prefixes()

        self.logger.info(f"\u001b[36;1m CONNECTED \u001b[0m [{self.bot.shard_count} Shards] [{len(self.bot.cogs)} Cogs]")

    @commands.Cog.listener()
    async def on_message(self, m):
        if  m.content.startswith('<@!639498607632056321>'):
            prefix = '/'
            if m.guild is not None:
                prefix = await self.d.prefix_cache.get(m.guild.id, '/')

            embed = discord.Embed(
                color=self.d.cc,
                description=f'The prefix for this server is ``{prefix}`` and the help command is ``{prefix}help``\n'
                            f'If you are in need of more help, you can join the **[Support Server]({self.d.support})**.'
            )
            embed.set_footer('Made by Iapetus11#6821')

            await ctx.send(embed=embed)
        elif 'emerald' in m.content:
            if m.guild is not None:
                guild = await self.db.fetch_guild(m.guild.id)

            if guild['replies']:
                await ctx.send(random.choice(self.d.hmms))
        elif '@someone' in m.content and m.guild is not None:
            someones = [u for u in m.guild.members if (not u.bot and u.status == discord.Status.online and m.author.id != u.id)]
            if len(someones) > 0:
            await m.channel.send(random.choice(someones).mention)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, e):
        # errors to ignore
        for e_type in (commands.CommandNotFound, commands.NotOwner, discord.errors.Forbidden,):
            if isinstance(e, e_type):
                return

        if isinstance(e, commands.CommandOnCooldown):
            seconds = round(e.retry_after, 2)

            if seconds == 0:
                await ctx.reinvoke()
                return

            hours = int(seconds / 3600)
            minutes = int(seconds / 60) % 60
            seconds -= round((hours * 60 * 60) + (minutes * 60), 2)

            time = ''
            if hours > 0: time += f'{hours} hours, '
            if minutes > 0: time += f'{minutes} minutes, '
            time += f'{seconds} seconds'

            await self.bot.send(random.choice(ctx.l.misc.cooldown_msgs).format(time))
        elif isinstance(e, commands.NoPrivateMessage):
            await self.bot.send(ctx.l.misc.errors.private)
        elif isinstance(e, commands.MissingPermissions):
            await self.bot.send(ctx.l.misc.errors.user_perms)
        elif isinstance(e, commands.BotMissingPermissions):
            await self.bot.send(ctx.l.misc.errors.bot_perms)
        elif isinstance(e, commands.MaxConcurrencyReached):
            await self.bot.send(ctx.l.misc.errors.concurrency)
        elif isinstance(e, commands.MissingRequiredArgument):
            await self.bot.send(ctx.l.misc.errors.missing_arg)
        elif isinstance(e, commands.BadArgument) or isinstance(e, commands.errors.ExpectedClosingQuoteError):
            await self.bot.send(ctx.l.misc.errors.bad_arg)
        else:
            traceback_text = ''.join(traceback.format_exception(type(e), e, e.__traceback__, 4))
            final = f'{ctx.author}: {ctx.message.content}\n\n{traceback_text}'
            await self.bot.send(self.bot.get_channel(642446655022432267), f'```{final[:1023 - 6]}```')


def setup(bot):
    bot.add_cog(Events(bot))
