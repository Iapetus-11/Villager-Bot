from discord.ext import commands
import discord
import aiohttp


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.ses = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.ses.close())

    @commands.command(name='meme')
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def meme(self, ctx):
        do_nsfw = False
        if isinstance(ctx.channel, discord.TextChannel):
            do_nsfw = ctx.channel.is_nsfw()

        meme = {'nsfw': True, 'spoiler': True}

        while meme['spoiler'] or (not do_nsfw and meme['nsfw']):
            meme = (await self.ses.get('https://meme-api.herokuapp.com/gimme/meme+memes+me_irl+dankmemes')).json()

        embed = discord.Embed(color=self.bot.cc, title=meme['title'], url=meme['postLink'])
        embed.set_image(url=meme['url'])

        await ctx.send(embed=embed)

    @commands.command(name='4chan')
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def greentext(self, ctx):
        do_nsfw = False
        if isinstance(ctx.channel, discord.TextChannel):
            do_nsfw = ctx.channel.is_nsfw()

        jj = {'nsfw': True, 'spoiler': True}

        while not do_nsfw and jj['nsfw']:
            jj = (await self.ses.get('https://meme-api.herokuapp.com/gimme/greentext')).json()

        embed = discord.Embed(color=self.bot.cc, title=jj['title'], url=jj['postLink'])
        embed.set_image(url=jj['url'])

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Fun(bot))
