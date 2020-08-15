from discord.ext import commands
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



def setup(bot):
    bot.add_cog(Events(bot))
