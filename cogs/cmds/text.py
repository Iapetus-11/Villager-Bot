import discord
from discord.ext import commands


class Text(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def lang_convert(self, msg, lang):
        keys = list(lang)

        for key in keys:
            msg = msg.replace(key, lang[key])

        if len(msg) > 2000 - 6:
            return
        else:
            return msg

    @commands.command(name='say')
    async def say_text(self, ctx, *, _text):
        """Sends whatever is put into the command"""

        try:
            await ctx.message.delete()
        except Exception:
            pass

        await ctx.send(ctx.message.clean_content.replace(f'{ctx.prefix}say ', '\uFEFF'))

    @commands.command(name='villagerspeak')
    async def villager_speak(self, ctx, *, msg):
        """Turns the given text into Minecraft villager sounds as text"""

        msg = ctx.message.clean_content.replace(f'{ctx.prefix}villagerspeak ', '\uFEFF')

        translated = await self.lang_convert(discord.utils.escape_markdown(msg), self.bot.fun_langs['villager'])

        if translated is None:
            await self.bot.send(ctx, 'The message is too long to convert.')
        else:
            await ctx.send(translated)

    @commands.command(name='enchant')
    async def enchant_lang(self, ctx, *, msg):
        """Turns regular text into the Minecraft enchantment table language"""

        translated = await self.lang_convert(discord.utils.escape_markdown(msg), self.bot.fun_langs['enchant'])

        if translated is None:
            await self.bot.send(ctx, 'The message is too long to convert.')
        else:
            await self.bot.send(ctx, f'```{translated}```')

    @commands.command(name='unenchant')
    async def unenchant_lang(self, ctx, *, msg):
        """Turns the Minecraft enchantment table language back into regular text"""

        translated = await self.lang_convert(discord.utils.escape_markdown(msg), self.bot.fun_langs['unenchant'])

        if translated is None:
            await self.bot.send(ctx, 'The message is too long to convert.')
        else:
            await self.bot.send(ctx, f'```{translated}```')

    @commands.command(name='sarcastic')
    async def sarcastic_text(self, ctx, *, msg):
        """Turns regular text into "sarcastic" text from spongebob"""

        msg = discord.utils.escape_markdown(ctx.message.clean_content.replace(f'{ctx.prefix}sarcastic ', '\uFEFF'))

        if len(msg) > 2000:
            await self.bot.send(ctx, 'The message is too long to convert.')
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

        clapped = discord.utils.escape_markdown(message.clean_content.replace(f'{ctx.prefix}clap ', '\uFEFF'))
        clapped = ':clap: ' + ':clap: '.join(clapped.split(' ')) + ' :clap:'

        if len(clapped) > 2000:
            await self.bot.send(ctx, 'The message is too long to convert.')
            return

        await ctx.send(clapped)


def setup(bot):
    bot.add_cog(Text(bot))
