from discord.ext import commands
import classyjson as cj
import discord
import aiohttp
import random
import typing


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.d = self.bot.d

        self.ses = aiohttp.ClientSession(loop=self.bot.loop)

    def cog_unload(self):
        self.bot.loop.create_task(self.ses.close())

    async def lang_convert(self, msg, lang):
        keys = list(lang)

        for key in keys:
            msg = msg.replace(key, lang.get(key))
            try:
                msg = msg.replace(key.upper(), lang.get(key).upper())
            except Exception:
                pass

        if len(msg) > 2000 - 6:
            return
        else:
            return discord.utils.escape_markdown(msg)

    async def nice(self, ctx):
        cmd_len = len(f'{ctx.prefix}{ctx.invoked_with} ')
        return ctx.message.clean_content[cmd_len:]

    @commands.command(name='meme', aliases=['meemee', 'meem', 'maymay', 'mehmeh'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def meme(self, ctx):
        """Sends a meme from reddit"""

        do_nsfw = False
        if isinstance(ctx.channel, discord.TextChannel):
            do_nsfw = ctx.channel.is_nsfw()

        meme = {'nsfw': True, 'spoiler': True}

        async with ctx.typing():
            while meme['spoiler'] or (not do_nsfw and meme['nsfw']):
                resp = await self.ses.get(
                    'https://betterapi.net/reddit/gimme/meme+memes+me_irl+dankmemes+wholesomememes+prequelmemes',
                    headers={'Authorization': self.d.vb_api_key}
                )
                meme = cj.classify(await resp.json())

        embed = discord.Embed(color=self.d.cc, title=f'{meme.title}', url=meme.permalink)
        embed.set_footer(text=f'{meme.upvotes}  |  u/{meme.author}', icon_url=self.bot.get_emoji(int(self.d.emojis.updoot.split(':')[-1].replace('>', ''))).url)
        embed.set_image(url=meme.url)

        await ctx.send(embed=embed)

    @commands.command(name='4chan', aliases=['greentext'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def greentext(self, ctx):
        """Sends a greentext from r/greentext"""

        do_nsfw = False
        if isinstance(ctx.channel, discord.TextChannel):
            do_nsfw = ctx.channel.is_nsfw()

        jj = {'nsfw': True}

        async with ctx.typing():
            while not do_nsfw and jj['nsfw']:
                resp = await self.ses.get(
                    'https://betterapi.net/reddit/gimme/4chan+greentext',
                    headers={'Authorization': self.d.vb_api_key}
                )
                jj = await resp.json()

        embed = discord.Embed(color=self.d.cc)
        embed.set_image(url=jj['url'])

        await ctx.send(embed=embed)

    @commands.command(name='comic')
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def comic(self, ctx):
        """Sends a comic from r/comics"""

        do_nsfw = False
        if isinstance(ctx.channel, discord.TextChannel):
            do_nsfw = ctx.channel.is_nsfw()

        jj = {'nsfw': True}

        async with ctx.typing():
            while not do_nsfw and jj['nsfw']:
                resp = await self.ses.get(
                    'https://betterapi.net/reddit/gimme/comics',
                    headers={'Authorization': self.d.vb_api_key}
                )
                jj = await resp.json()

        embed = discord.Embed(color=self.d.cc)
        embed.set_image(url=jj['url'])

        await ctx.send(embed=embed)

    @commands.command(name='cursed', aliases=['cursedmc'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def cursed_mc(self, ctx):
        async with ctx.typing():
            if random.choice((True, False,)):
                jj = {'nsfw': True}

                while jj['nsfw']:
                    resp = await self.ses.get(
                        'https://betterapi.net/reddit/gimme/CursedMinecraft',
                        headers={'Authorization': self.d.vb_api_key}
                    )
                    jj = await resp.json()

                embed = discord.Embed(color=self.d.cc)
                embed.set_image(url=jj['url'])

                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(color=self.d.cc)
                embed.set_image(url=f'{self.d.base_url}/images/cursed_minecraft/{random.choice(self.d.cursed_images)}')

                await ctx.send(embed=embed)

    @commands.command(name='say')
    async def say_text(self, ctx, *, _text):
        """Sends whatever is put into the command"""

        try:
            await ctx.message.delete()
        except Exception:
            pass

        await ctx.send(await self.nice(ctx))

    @commands.command(name='villagerspeak')
    async def villager_speak(self, ctx, *, msg):
        """Turns the given text into Minecraft villager sounds as text"""

        translated = await self.lang_convert(await self.nice(ctx), self.d.fun_langs['villager'])

        if translated is None:
            await self.bot.send(ctx, ctx.l.fun.too_long)
        else:
            await ctx.send(translated)

    @commands.command(name='enchant')
    async def enchant_lang(self, ctx, *, msg):
        """Turns regular text into the Minecraft enchantment table language"""

        translated = await self.lang_convert((await self.nice(ctx)).lower(), self.d.fun_langs['enchant'])

        if translated is None:
            await self.bot.send(ctx, ctx.l.fun.too_long)
        else:
            await ctx.send(translated)

    @commands.command(name='unenchant')
    async def unenchant_lang(self, ctx, *, msg):
        """Turns the Minecraft enchantment table language back into regular text"""

        translated = await self.lang_convert(await self.nice(ctx), self.d.fun_langs['unenchant'])

        if translated is None:
            await self.bot.send(ctx, ctx.l.fun.too_long)
        else:
            await ctx.send(translated)

    @commands.command(name='vaporwave')
    async def vaporwave_text(self, ctx, *, msg):
        """Turns regular text into vaporwave text"""

        translated = await self.lang_convert(await self.nice(ctx), self.d.fun_langs['vaporwave'])

        if translated is None:
            await self.bot.send(ctx, ctx.l.fun.too_long)
        else:
            await ctx.send(translated)

    @commands.command(name='sarcastic')
    async def sarcastic_text(self, ctx, *, msg):
        """Turns regular text into "sarcastic" text from spongebob"""

        msg = await self.nice(ctx)

        if len(msg) > 2000:
            await self.bot.send(ctx, ctx.l.fun.too_long)
            return

        caps = True
        sarcastic = ''

        for letter in msg:
            if not letter == ' ': caps = not caps

            if caps:
                sarcastic += letter.upper()
            else:
                sarcastic += letter.lower()

        await ctx.send(sarcastic)

    @commands.command(name='clap')
    async def clap_cheeks(self, ctx, *, text):
        """Puts the :clap: emoji between words"""

        clapped = ':clap: ' + ' :clap: '.join((await self.nice(ctx)).split(' ')) + ' :clap:'

        if len(clapped) > 2000:
            await self.bot.send(ctx, ctx.l.fun.too_long)
            return

        await ctx.send(clapped)

    @commands.command(name='emojify')
    async def emojifi_text(self, ctx, *, _text):
        """Turns text into emojis"""

        abcdefg_someone_shouldve_told_ya_not_to_fuck_with_me = 'abcdefghijklmnopqrstuvwxyz'

        text = ''

        for letter in (await self.nice(ctx)).lower():
            if letter in abcdefg_someone_shouldve_told_ya_not_to_fuck_with_me:
                text += f':regional_indicator_{letter}: '
            else:
                text += self.d.emojified.get(letter, letter) + ' '

        if len(text) > 2000:
            await self.bot.send(ctx, ctx.l.fun.too_long)
        else:
            await ctx.send(text)

    @commands.command(name='owo', aliases=['owofy'])
    async def owofy_text(self, ctx, *, text):
        """Make any string more cringe"""

        text = text.lower().replace('l', 'w').replace('r', 'w')

        await ctx.send(f'{text} {random.choice(self.d.owos)}')

    @commands.command(name='bubblewrap', aliases=['pop'])
    async def bubblewrap(self, ctx, size=None):
        """Sends bubblewrap to the chat"""

        if size is None:
            size = (10, 10,)
        else:
            size = size.split('x')

            if len(size) != 2:
                await self.bot.send(ctx, ctx.l.fun.bubblewrap.invalid_size_1)
                return

            try:
                size[0] = int(size[0])
                size[1] = int(size[1])
            except ValueError:
                await self.bot.send(ctx, ctx.l.fun.bubblewrap.invalid_size_1)
                return

            for val in size:
                if val < 1 or val > 12:
                    await self.bot.send(ctx, ctx.l.fun.bubblewrap.invalid_size_2)
                    return

        bubble = '||**pop**||'
        await self.bot.send(ctx, f'{bubble*size[0]}\n'*size[1])

    @commands.command(name='kill', aliases=['die', 'kil', 'dorito'])
    async def kill_thing(self, ctx, *, thing: typing.Union[discord.User, str]):
        if isinstance(thing, discord.User):
            thing = thing.mention

        await self.bot.send(ctx, random.choice(self.d.kills).format(thing, ctx.author.mention))

    @commands.command(name='coinflip', aliases=['flipcoin', 'cf'])
    async def coin_flip(self, ctx):
        await self.bot.send(ctx, random.choice(('heads', 'tails')))


def setup(bot):
    bot.add_cog(Fun(bot))
