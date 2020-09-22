from discord.ext import commands
import discord


class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = self.bot.d

        self.db = self.bot.db

    @commands.group(name='config', aliases=['settings', 'conf'])
    @commands.guild_only()
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def config(self, ctx):
        if ctx.invoked_subcommand is None:
            ctx.reset_cooldown(ctx)

            embed = discord.Embed(color=self.d.cc, title='__**Villager Bot Settings**__')

            guild_conf = 'Change the server prefix - `{0}config prefix <newprefix>`\n' \
                         'Change whether bot should respond to "emeralds" - `{0}config replies <on/off>`\n' \
                         'Changes the difficulty of mobs, and some other things - `{0}config difficulty <peaceful/easy/hard>`\n' \
                         'Changes the language that Villager Bot is in - `{0}config lang <language>`\n'

            embed.add_field(name='Server/Guild Configuration', value=guild_conf)

            #user_conf = 'bruh2.0'
            #embed.add_field(name='Per User Configuration', value=user_conf)

            await ctx.send(embed=embed)

    @config.command(name='prefix')
    async def config_prefix(self, ctx, prefix=None):
        if prefix is None:
            prev = self.d.prefix_cache.get(ctx.guild.id, self.bot.d.default_prefix)
            await self.bot.send(ctx, f'The prefix in this server is: `{prev}`')
            return

        if len(prefix) > 15:
            await self.bot.send(ctx, 'You cannot have a prefix longer than `15` characters.')
            return

        for char in prefix:
            if char not in self.d.acceptable_prefix_chars:
                await self.bot.send(ctx, f'`{char}` is not allowed in a prefix.')
                return

        await self.db.set_prefix(ctx.guild.id, prefix)
        await self.bot.send(ctx, f'Set the server prefix to `{prefix}`')

    @config.command(name='replies')
    async def config_replies(self, ctx, replies=None):
        if replies is None:
            guild = await self.db.fetch_guild(ctx.guild.id)
            await self.bot.send(ctx, f'Message replies (like to "emerald") are {"enabled"*guild["replies"] + "disabled"*(not guild["replies"])}')
            return

        if replies.lower() in ('yes', 'true', 'on'):
            await self.db.set_guild_attr(ctx.guild.id, 'replies', True)
            await self.bot.send(ctx, 'Turned message replies `on`.')
        elif replies.lower() in ('no', 'false', 'off'):
            await self.db.set_guild_attr(ctx.guild.id, 'replies', False)
            await self.bot.send(ctx, 'Turned message replies `off`.')
        else:
            await self.bot.send(ctx, 'That\'s not a valid option. (Valid options are `on`, `off`)')

    @config.command(name='difficulty')
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


def setup(bot):
    bot.add_cog(Config(bot))
