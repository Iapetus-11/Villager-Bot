from urllib.parse import quote as urlquote
from discord.ext import commands
import classyjson as cj
import asyncio
import discord
import random
import typing

from util.code import format_exception
from util.misc import strip_command

try:
    from util import tiler_rgba
except ImportError as e:
    print(format_exception(e))
    tiler = None

ALPHABET_LOWER = "abcdefghijklmnopqrstuvwxyz"
INSULTS = {"i am stupid", "i am dumb", "i am very stupid", "i am very dumb", "i stupid", "i'm stupid", "i'm dumb"}


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = bot.d
        self.k = bot.k

        self.aiohttp = bot.aiohttp

        if tiler_rgba:
            self.tiler = tiler_rgba.TilerRGBA("data/emoji_palette.json")
        else:
            self.tiler = None

    def lang_convert(self, msg, lang):
        keys = list(lang)

        for key in keys:
            msg = msg.replace(key, lang.get(key))

            try:
                msg = msg.replace(key.upper(), lang.get(key).upper())
            except Exception:
                pass

        if len(msg) > 2000 - 6:
            raise ValueError("message is too big")

        return msg

    @commands.command(name="meme", aliases=["meemee", "meem", "maymay", "mehmeh"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def meme(self, ctx):
        """Sends a meme from reddit"""

        do_nsfw = False

        if isinstance(ctx.channel, discord.TextChannel):
            do_nsfw = ctx.channel.is_nsfw()

        meme = {"nsfw": True, "spoiler": True}

        async with ctx.typing():
            while meme["spoiler"] or (not do_nsfw and meme["nsfw"]) or meme.get("image") is None:
                resp = await self.aiohttp.get(
                    "https://api.iapetus11.me/reddit/meme",
                    headers={"Authorization": self.k.villager_api},
                    params={"queryId": ctx.channel.id},
                )

                meme = cj.classify(await resp.json())

        embed = discord.Embed(color=self.d.cc, title=meme.title[:256], url=meme.permalink)

        embed.set_footer(text=f"{meme.upvotes}  |  u/{meme.author}", icon_url=self.d.upvote_emoji_image)
        embed.set_image(url=meme.image)

        await ctx.send(embed=embed)

    @commands.command(name="4chan", aliases=["greentext"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def greentext(self, ctx):
        """Sends a greentext from r/greentext"""

        do_nsfw = False

        if isinstance(ctx.channel, discord.TextChannel):
            do_nsfw = ctx.channel.is_nsfw()

        jj = {"nsfw": True}

        async with ctx.typing():
            while (not do_nsfw and jj["nsfw"]) or jj.get("image") is None:
                resp = await self.aiohttp.get(
                    "https://api.iapetus11.me/reddit/greentext",
                    headers={"Authorization": self.k.villager_api},
                    params={"queryId": ctx.channel.id},
                )

                jj = await resp.json()

        embed = discord.Embed(color=self.d.cc)
        embed.set_image(url=jj["image"])

        await ctx.send(embed=embed)

    @commands.command(name="comic")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def comic(self, ctx):
        """Sends a comic from r/comics"""

        do_nsfw = False
        if isinstance(ctx.channel, discord.TextChannel):
            do_nsfw = ctx.channel.is_nsfw()

        comic = {"nsfw": True, "spoiler": True}

        async with ctx.typing():
            while comic["spoiler"] or (not do_nsfw and comic["nsfw"]) or comic.get("image") is None:
                resp = await self.aiohttp.get(
                    "https://api.iapetus11.me/reddit/comic",
                    headers={"Authorization": self.k.villager_api},
                    params={"queryId": ctx.channel.id},
                )

                comic = cj.classify(await resp.json())

        embed = discord.Embed(color=self.d.cc, title=comic.title[:256], url=comic.permalink)

        embed.set_footer(text=f"{comic.upvotes}  |  u/{comic.author}", icon_url=self.d.upvote_emoji_image)
        embed.set_image(url=comic.image)

        await ctx.send(embed=embed)

    @commands.command(name="cursed", aliases=["cursedmc"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def cursed_mc(self, ctx):
        if random.choice((True, False)):
            meme = {"nsfw": True, "spoiler": True}

            async with ctx.typing():
                while meme["spoiler"] or meme["nsfw"] or meme.get("image") is None:
                    resp = await self.bot.aiohttp.get(
                        "https://api.iapetus11.me/reddit/cursedminecraft",
                        headers={"Authorization": self.k.villager_api},
                        params={"queryId": ctx.channel.id},
                    )

                    meme = cj.classify(await resp.json())

            embed = discord.Embed(color=self.d.cc, title=meme.title[:256], url=meme.permalink)

            embed.set_footer(text=f"{meme.upvotes}  |  u/{meme.author}", icon_url=self.d.upvote_emoji_image)
            embed.set_image(url=meme.image)

            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(color=self.d.cc)
            embed.set_image(url=f"https://iapetus11.me/static/images/cursed_minecraft/{random.choice(self.d.cursed_images)}")

            await ctx.send(embed=embed)

    @commands.command(name="say")
    async def say_text(self, ctx, *, text):
        """Sends whatever is put into the command"""

        nice = strip_command(ctx)

        if nice.lower() in INSULTS:
            await ctx.reply("Yes.")
            return

        try:
            await ctx.message.delete()
        except Exception:
            pass

        await ctx.send(nice)

    @commands.command(name="villagerspeak")
    async def villager_speak(self, ctx, *, msg):
        """Turns the given text into Minecraft villager sounds as text"""

        try:
            translated = self.lang_convert(strip_command(ctx), self.d.fun_langs.villager)
            await ctx.send(translated)
        except ValueError:
            await self.bot.send_embed(ctx, ctx.l.fun.too_long)

    @commands.command(name="enchant")
    async def enchant_lang(self, ctx, *, msg):
        """Turns regular text into the Minecraft enchantment table language"""

        try:
            translated = self.lang_convert((strip_command(ctx)).lower(), self.d.fun_langs.enchant)
            await ctx.send(translated)
        except ValueError:
            await self.bot.send_embed(ctx, ctx.l.fun.too_long)

    @commands.command(name="unenchant")
    async def unenchant_lang(self, ctx, *, msg):
        """Turns the Minecraft enchantment table language back into regular text"""

        try:
            translated = self.lang_convert(strip_command(ctx), self.d.fun_langs.unenchant)
            await ctx.send(translated)
        except ValueError:
            await self.bot.send_embed(ctx, ctx.l.fun.too_long)

    @commands.command(name="vaporwave")
    async def vaporwave_text(self, ctx, *, msg):
        """Turns regular text into vaporwave text"""

        try:
            translated = self.lang_convert(strip_command(ctx), self.d.fun_langs.vaporwave)
            await ctx.send(translated)
        except ValueError:
            await self.bot.send_embed(ctx, ctx.l.fun.too_long)

    @commands.command(name="sarcastic")
    async def sarcastic_text(self, ctx, *, msg):
        """Turns regular text into "sarcastic" text from spongebob"""

        msg = strip_command(ctx)

        caps = True
        sarcastic = ""

        for letter in msg:
            if not letter == " ":
                caps = not caps

            if caps:
                sarcastic += letter.upper()
            else:
                sarcastic += letter.lower()

        await ctx.send(sarcastic)

    @commands.command(name="clap")
    async def clap_cheeks(self, ctx, *, text):
        """Puts the :clap: emoji between words"""

        clapped = ":clap: " + " :clap: ".join((strip_command(ctx)).split(" ")) + " :clap:"

        if len(clapped) > 2000:
            await self.bot.send_embed(ctx, ctx.l.fun.too_long)
            return

        await ctx.send(clapped)

    @commands.command(name="emojify")
    async def emojify(self, ctx, *, _text=None):
        """Turns text or images into emojis"""

        text = (strip_command(ctx)).lower()

        if len(ctx.message.attachments) > 0:
            image = ctx.message.attachments[0]

            if image.filename.lower()[-4:] not in (".jpg", ".png") and not image.filename.lower()[-5:] in (".jpeg"):
                await self.bot.reply_embed(ctx, ctx.l.minecraft.mcimage.stupid_2)
                return

            try:
                image.height
            except Exception:
                await self.bot.reply_embed(ctx, ctx.l.minecraft.mcimage.stupid_3)
                return

            detailed = False

            for detailed_keyword in ("large", "high", "big", "quality", "detailed"):
                if detailed_keyword in ctx.message.content:
                    detailed = True
                    break

            async with ctx.typing():
                image_data = await self.bot.loop.run_in_executor(
                    self.bot.tp, self.tiler.generate, await image.read(use_cached=True), 1600, detailed
                )

            await ctx.reply(file=discord.File(image_data, filename=image.filename), mention_author=False)
        elif text:
            for letter in text:
                if letter in ALPHABET_LOWER:
                    text += f":regional_indicator_{letter}: "
                else:
                    text += self.d.emojified.get(letter, letter) + " "

            if len(text) > 2000:
                await self.bot.send_embed(ctx, ctx.l.fun.too_long)
            else:
                await ctx.send(text)
        else:
            await self.bot.reply_embed(ctx, "You must add text or an image to be emojified.")

    @commands.command(name="owo", aliases=["owofy"])
    async def owofy_text(self, ctx, *, text):
        """Make any text more cringe"""

        text = text.lower().replace("l", "w").replace("r", "w")

        if len(text) > 1950:
            await self.bot.send_embed(ctx, ctx.l.fun.too_long)
        else:
            await ctx.send(f"{text} {random.choice(self.d.owos)}")

    @commands.command(name="bubblewrap", aliases=["pop"])
    async def bubblewrap(self, ctx, size=None):
        """Sends bubblewrap to the chat"""

        if size is None:
            size = (10, 10)
        else:
            size = size.split("x")

            if len(size) != 2:
                await self.bot.send_embed(ctx, ctx.l.fun.bubblewrap.invalid_size_1)
                return

            try:
                size[0] = int(size[0])
                size[1] = int(size[1])
            except ValueError:
                await self.bot.send_embed(ctx, ctx.l.fun.bubblewrap.invalid_size_1)
                return

            for val in size:
                if val < 1 or val > 12:
                    await self.bot.send_embed(ctx, ctx.l.fun.bubblewrap.invalid_size_2)
                    return

        bubble = "||**pop**||"
        await self.bot.send_embed(ctx, f"{bubble*size[0]}\n" * size[1])

    @commands.command(name="kill", aliases=["die", "kil", "dorito"])
    async def kill_thing(self, ctx, *, thing: typing.Union[discord.Member, str]):
        if isinstance(thing, discord.Member):
            thing = thing.mention

        await self.bot.send_embed(ctx, random.choice(self.d.kills).format(thing[:500], ctx.author.mention))

    @commands.command(name="coinflip", aliases=["flipcoin", "cf"])
    async def coin_flip(self, ctx):
        await self.bot.send_embed(ctx, random.choice(("heads", "tails")))

    @commands.command(name="pat")
    @commands.guild_only()
    async def pat(self, ctx, users: commands.Greedy[discord.Member] = [], *, text: str = ""):
        resp = await self.bot.aiohttp.get("https://rra.ram.moe/i/r?type=pat")
        image_url = "https://rra.ram.moe" + (await resp.json())["path"]

        embed = discord.Embed(
            color=self.d.cc,
            title=f"**{discord.utils.escape_markdown(ctx.author.display_name)}** pats {', '.join(f'**{discord.utils.escape_markdown(u.display_name)}**' for u in users)} {text}"[
                :256
            ],
        )
        embed.set_image(url=image_url)

        await ctx.send(embed=embed)

    @commands.command(name="slap")
    @commands.guild_only()
    async def slap(self, ctx, users: commands.Greedy[discord.Member] = [], *, text: str = ""):
        resp = await self.bot.aiohttp.get("https://rra.ram.moe/i/r?type=slap")
        image_url = "https://rra.ram.moe" + (await resp.json())["path"]

        embed = discord.Embed(
            color=self.d.cc,
            title=f"**{discord.utils.escape_markdown(ctx.author.display_name)}** slaps {', '.join(f'**{discord.utils.escape_markdown(u.display_name)}**' for u in users)} {text}"[
                :256
            ],
        )
        embed.set_image(url=image_url)

        await ctx.send(embed=embed)

    @commands.command(name="achievement", aliases=["mcachieve"])
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def minecraft_achievement(self, ctx, *, text):
        url = f"https://api.iapetus11.me/mc/achievement/{urlquote(text[:26])}"
        embed = discord.Embed(color=self.d.cc)

        embed.description = ctx.l.fun.dl_img.format(url)
        embed.set_image(url=url)

        await ctx.send(embed=embed)

    @commands.command(name="splashtext", aliases=["mcsplash", "splashscreen", "splash"])
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def minecraft_splash_screen(self, ctx, *, text):
        url = f"https://api.iapetus11.me/mc/splash/{urlquote(text[:27])}"
        embed = discord.Embed(color=self.d.cc)

        embed.description = ctx.l.fun.dl_img.format(url)
        embed.set_image(url=url)

        await ctx.send(embed=embed)

    @commands.command(name="trivia", aliases=["mctrivia"])
    @commands.max_concurrency(1, per=commands.BucketType.channel)
    async def minecraft_trivia(self, ctx):
        question = random.choice(ctx.l.fun.trivia.questions)
        correct_choice = question.a[0]

        choices = question.a.copy()
        random.shuffle(choices)

        embed = discord.Embed(
            color=self.d.cc,
            title=ctx.l.fun.trivia.title.format(self.d.emojis.bounce, ctx.l.fun.trivia.difficulty[question.d], ":question:"),
        )
        embed.description = f"*{question.q}*"
        embed.set_footer(text="\uFEFF\n" + ctx.l.fun.trivia.time_to_answer)

        for i, c in enumerate(choices):
            embed.add_field(name="\uFEFF", value=f"**{i+1}.** {c}")

            if i % 2 == 0:
                embed.add_field(name="\uFEFF", value="\uFEFF")

        msg = await ctx.send(embed=embed)

        for i in range(len(choices)):
            await msg.add_reaction(self.d.emojis.numbers[i + 1])

        def reaction_check(react, r_user):
            return (
                r_user == ctx.author
                and ctx.channel == react.message.channel
                and msg == react.message
                and react.emoji in self.d.emojis.numbers[1 : len(choices) + 1]
            )

        try:
            react, r_user = await self.bot.wait_for("reaction_add", check=reaction_check, timeout=15)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                color=self.d.cc,
                title=ctx.l.fun.trivia.title_basic.format(self.d.emojis.bounce, ":question:"),
                description=ctx.l.fun.trivia.timeout,
            )
            await msg.edit(embed=embed)
            return
        finally:
            try:
                await msg.clear_reactions()
            except Exception:
                pass

        embed = discord.Embed(
            color=self.d.cc,
            title=ctx.l.fun.trivia.title_basic.format(self.d.emojis.bounce, ":question:"),
        )

        if choices[self.d.emojis.numbers.index(react.emoji) - 1] == correct_choice:
            emeralds_won = int((random.random() + 0.75) * (question.d + 1) * 15)
            await self.db.balance_add(ctx.author.id, emeralds_won)
            embed.description = random.choice(ctx.l.fun.trivia.correct).format(emeralds_won, self.d.emojis.emerald)
        else:
            embed.description = random.choice(ctx.l.fun.trivia.incorrect)

        await msg.edit(embed=embed)


def setup(bot):
    bot.add_cog(Fun(bot))
