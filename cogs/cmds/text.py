import discord
from discord.ext import commands
import random


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

    async def nice(ctx):
        cmd_len = len(f'{ctx.prefix}{ctx.invoked_with} ')
        return ctx.message.clean_content[cmd_len:]

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

    @commands.command(name='bubblewrap', aliases=['pop'])
    async def bubblewrap(self, ctx, size=None):
        """Sends bubblewrap to the chat"""

        if size is None:
            size = (10, 10,)
        else:
            size = size.split('x')

            if len(size) != 2:
                await self.bot.send(ctx, 'That is not a valid size. Example of a valid size: 10x10')
                return

            try:
                size[0] = int(size[0])
                size[1] = int(size[1])
            except ValueError:
                await self.bot.send(ctx, 'That is not a valid size. Example of a valid size: 10x10')
                return

            for val in size:
                if val < 1 or val > 32:
                    await self.bot.send(ctx, 'The size must be between 1 and 32')
                    return

        bubbles = ['||*pop*||', '||pOp||', '||*pOp*||', '||***POP***||', '||PoP||', '||**pop**||', '||*POP*||']
        bubble_body = ''

        for i in range(size[1]):
            for j in range(size[0]):
                bubble_body += random.choice(bubbles)
            bubble_body += '\n'

        await self.bot.send(ctx, bubble_body)

    @commands.command(name='emojify')
    async def emojifi_text(self, ctx, *, _text):
        abcdefg_someone_shouldve_told_ya_not_to_fuck_with_me = 'abcdefghijklmnopqrstuvwxyz'

        text = discord.utils.escape_markdown(ctx.message.clean_content.replace('emojify', ''))

        for letter in text:
            if letter in abcdefg_someone_shouldve_told_ya_not_to_fuck_with_me:
                text += ':regional_indicator_' + letter
            else:
                text += self.bot.emojified.get(letter, letter)

        if len(text) > 2000:
            await self.bot.send(ctx, 'That would be too long to send')
        else:
            await ctx.send(text)


def setup(bot):
    bot.add_cog(Text(bot))
