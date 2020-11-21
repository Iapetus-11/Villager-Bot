from discord.ext import commands
import discord


class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = self.bot.d

        self.db = self.bot.get_cog('Database')

    @commands.group(name='config', aliases=['settings', 'conf'])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def config(self, ctx):
        if ctx.invoked_subcommand is None:
            ctx.command.reset_cooldown(ctx)

            embed = discord.Embed(color=self.d.cc)
            embed.set_author(name=ctx.l.config.main.title, icon_url=self.d.splash_logo)
            embed.add_field(name=ctx.l.config.main.guild_conf, value=''.join(ctx.l.config.main.guild_content).format(ctx.prefix))

            #user_conf = 'bruh2.0'
            #embed.add_field(name='Per User Configuration', value=user_conf)

            await ctx.send(embed=embed)

    @config.command(name='prefix')
    async def config_prefix(self, ctx, prefix=None):
        if prefix is None:
            prev = self.d.prefix_cache.get(ctx.guild.id, self.bot.d.default_prefix)
            await self.bot.send(ctx, ctx.l.config.prefix.this_server.format(prev))
            return

        if len(prefix) > 15:
            await self.bot.send(ctx, ctx.l.config.prefix.error_1.format(15))
            return

        for char in prefix:
            if char not in self.d.acceptable_prefix_chars:
                await self.bot.send(ctx, ctx.l.config.prefix.error_2.format(char))
                return

        await self.db.set_guild_attr(ctx.guild.id, 'prefix', prefix)
        self.d.prefix_cache[ctx.guild.id] = prefix
        await self.bot.send(ctx, ctx.l.config.prefix.set.format(prefix))

    @config.command(name='replies')
    async def config_replies(self, ctx, replies=None):
        if replies is None:
            guild = await self.db.fetch_guild(ctx.guild.id)
            state = ctx.l.config.replies.enabled*guild['replies'] + ctx.l.config.replies.disabled*(not guild['replies'])
            await self.bot.send(ctx, ctx.l.config.replies.this_server.format(state))
            return

        if replies.lower() in ('yes', 'true', 'on'):
            await self.db.set_guild_attr(ctx.guild.id, 'replies', True)
            await self.bot.send(ctx, ctx.l.config.replies.set.format('on'))
        elif replies.lower() in ('no', 'false', 'off'):
            await self.db.set_guild_attr(ctx.guild.id, 'replies', False)
            await self.bot.send(ctx, ctx.l.config.replies.set.format('off'))
        else:
            await self.bot.send(ctx, ctx.l.config.invalid.format('`on`, `off`'))

    @config.command(name='difficulty', aliases=['diff'])
    async def config_difficulty(self, ctx, diff=None):
        if diff is None:
            guild = await self.db.fetch_guild(ctx.guild.id)
            await self.bot.send(ctx, ctx.l.config.diff.this_server.format(guild['difficulty']))
            return

        if diff.lower() == 'peaceful':
            await self.db.set_guild_attr(ctx.guild.id, 'difficulty', 'peaceful')
            await self.bot.send(ctx, ctx.l.config.diff.set.format('peaceful'))
        elif diff.lower() == 'easy':
            await self.db.set_guild_attr(ctx.guild.id, 'difficulty', 'easy')
            await self.bot.send(ctx, ctx.l.config.diff.set.format('easy'))
        elif diff.lower() == 'hard':
            await self.db.set_guild_attr(ctx.guild.id, 'difficulty', 'hard')
            await self.bot.send(ctx, ctx.l.config.diff.set.format('hard'))
        else:
            await self.bot.send(ctx, ctx.l.config.invalid.format('`peaceful`, `easy`, `hard`'))

    @config.command(name='language', aliases=['lang'])
    async def config_language(self, ctx, lang=None):
        if lang is None:
            guild = await self.db.fetch_guild(ctx.guild.id)
            await self.bot.send(ctx, ctx.l.config.lang.this_server.format(guild['lang'].replace('_', '-')))
            return

        lang_codes = [l.replace('_', '-') for l in list(self.bot.langs)]

        if lang.lower() in lang_codes:
            await self.db.set_guild_attr(ctx.guild.id, 'lang', lang.replace('-', '_'))
            self.d.lang_cache[ctx.guild.id] = lang.replace('-', '_')
            await self.bot.send(ctx, ctx.l.config.lang.set.format(lang.lower()))
        else:
            await self.bot.send(ctx, ctx.l.config.invalid.format('`{}`'.format('`, `'.join(lang_codes))))

    @config.command(name='defaultserver', aliases=['defaultmcserver', 'mcserver'])
    async def config_default_mcserver(self, ctx, mcserver=None):
        if mcserver is None:
            guild = await self.db.fetch_guild(ctx.guild.id)
            await self.bot.send(ctx, ctx.l.config.mcs.this_server.format(guild['mcserver']))
            return

        if len(mcserver) > 30:
            await self.bot.send(ctx, ctx.l.config.mcs.error_1.format(30))
            return

        await self.db.set_guild_attr(ctx.guild.id, 'mcserver', mcserver)
        await self.bot.send(ctx, ctx.l.config.mcs.set.format(mcserver))


def setup(bot):
    bot.add_cog(Config(bot))
