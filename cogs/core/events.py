from discord.ext import commands
import traceback
import discord
import logging
import random


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.d = self.bot.d

        self.logger = logging.getLogger("Events")
        self.logger.setLevel(logging.INFO)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(activity=discord.Game(name=random.choice(self.d.playing_list)))
        self.logger.info(f"\u001b[36;1m CONNECTED \u001b[0m [{self.bot.shard_count} Shards] [{len(self.bot.cogs)} Cogs]")

    @commands.Cog.listener()
    async def on_message(self, m):
        if '@someone' in m.content and m.guild is not None:
            someones = [u for u in m.guild.members if (not u.bot and u.status == discord.Status.online and m.author.id != u.id)]
            if len(someones) > 0:
                await m.channel.send(random.choice(someones).mention)
        elif m.content.startswith('<@!639498607632056321>'):
            prefix = '!!'
            if m.guild is not None:
                prefix = await self.db.fetch_prefix(ctx.guild.id)

            embed = discord.Embed(
                color=self.d.cc,
                description=f'The prefix for this server is ``{prefix}`` and the help command is ``{prefix}help``\n'
                            f'If you are in need of more help, you can join the **[Support Server]({self.d.support})**.'
            )
            embed.set_footer('Made by Iapetus11#6821')

            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, e):
        # errors to ignore
        for e_type in (commands.CommandNotFound, commands.NotOwner, discord.errors.Forbidden,):
            if isinstance(e, e_type):
                return

        traceback_text = ''.join(traceback.format_exception(type(e), e, e.__traceback__, 4))
        final = f'{ctx.author}: {ctx.message.content}\n\n{traceback_text}'
        await self.bot.send(ctx, f'```{final[:1023 - 6]}```')



def setup(bot):
    bot.add_cog(Events(bot))
