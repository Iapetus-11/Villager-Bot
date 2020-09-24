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

            embed = discord.Embed(color=self.d.cc, title=ctx.l.config.main.title)

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
            await self.bot.send(ctx, f'Message replies (like to "emerald") are `{"enabled"*guild["replies"] + "disabled"*(not guild["replies"])}`')
            return

        if replies.lower() in ('yes', 'true', 'on'):
            await self.db.set_guild_attr(ctx.guild.id, 'replies', True)
            await self.bot.send(ctx, 'Turned message replies `on`.')
        elif replies.lower() in ('no', 'false', 'off'):
            await self.db.set_guild_attr(ctx.guild.id, 'replies', False)
            await self.bot.send(ctx, 'Turned message replies `off`.')
        else:
            await self.bot.send(ctx, 'That\'s not a valid option. (Valid options are `on`, `off`)')

    @config.command(name='difficulty', aliases=['diff'])
    async def config_difficulty(self, ctx, diff=None):
        if diff is None:
            guild = await self.db.fetch_guild(ctx.guild.id)
            await self.bot.send(ctx, f'The server difficulty is currently set to `{guild["difficulty"]}`.')
            return

        if diff.lower() == 'peaceful':
            await self.db.set_guild_attr(ctx.guild.id, 'difficulty', 'peaceful')
            await self.bot.send(ctx, 'Set the server difficulty to `peaceful`.')
        elif diff.lower() == 'easy':
            await self.db.set_guild_attr(ctx.guild.id, 'difficulty', 'easy')
            await self.bot.send(ctx, 'Set the server difficulty to `easy`.')
        elif diff.lower() == 'hard':
            await self.db.set_guild_attr(ctx.guild.id, 'difficulty', 'hard')
            await self.bot.send(ctx, 'Set the server difficulty to `hard`.')
        else:
            await self.bot.send(ctx, 'That\'s not a valid option. (Valid options are `peaceful`, `easy`, `hard`)')

    @config.command(name='language', aliases=['lang'])
    async def config_language(self, ctx, lang=None):
        if lang is None:
            guild = await self.db.fetch_guild(ctx.guild.id)
            await self.bot.send(ctx, f'The server language is currently set to `{guild["lang"].replace("_", "-")}`.')
            return

        lang_codes = [l.replace('_', '-') for l in list(self.bot.langs)]

        if lang.lower() in lang_codes:
            await self.db.set_guild_attr(ctx.guild.id, 'lang', lang.replace('-', '_'))
            self.d.lang_cache[ctx.guild.id] = lang.replace('-', '_')
            await self.bot.send(ctx, f'Set the server language to `{lang.lower()}`.')
        else:
            await self.bot.send(ctx, 'That\'s not a valid option. (Valid options are: `{}`)'.format('`, `'.join(lang_codes)))


def setup(bot):
    bot.add_cog(Config(bot))
