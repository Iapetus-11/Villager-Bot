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
            await self.bot.send(f'The prefix in this server is: `{prev}`')
            return

        


def setup(bot):
    bot.add_cog(Config(bot))
