import asyncio
import random
import typing
from contextlib import suppress
from urllib.parse import quote as urlquote

import classyjson as cj
import disnake
from disnake.ext import commands
from util.ctx import Ctx
from util.ipc import PacketType
from util.misc import SuppressCtxManager, strip_command

from bot import VillagerBotCluster

ALPHABET_LOWER = "abcdefghijklmnopqrstuvwxyz"
INSULTS = {"i am stupid", "i am dumb", "i am very stupid", "i am very dumb", "i stupid", "i'm stupid", "i'm dumb"}


class Fun(commands.Cog):
    def __init__(self, bot: VillagerBotCluster):
        self.bot = bot

        self.d = bot.d
        self.k = bot.k

        self.aiohttp = bot.aiohttp
        self.db = bot.get_cog("Database")
        self.ipc = bot.ipc

    def lang_convert(self, msg, lang):
        keys = list(lang)

        for key in keys:
            msg = msg.replace(key, lang.get(key))

            with suppress(Exception):
                msg = msg.replace(key.upper(), lang.get(key).upper())

        if len(msg) > 2000 - 6:
            raise ValueError("message is too big")

        return msg

    @commands.command(name="meme", aliases=["meemee", "meem", "maymay", "mehmeh"])
    @commands.cooldown(1, 1.5, commands.BucketType.user)
    async def meme(self, ctx: Ctx):
        """Sends a meme from reddit"""

        do_nsfw = False

        if isinstance(ctx.channel, disnake.TextChannel):
            do_nsfw = ctx.channel.is_nsfw()

        meme = {"nsfw": True, "spoiler": True}

        async with SuppressCtxManager(ctx.typing()):
            while meme["spoiler"] or (not do_nsfw and meme["nsfw"]) or meme.get("image") is None:
                resp = await self.aiohttp.get(
                    "https://api.iapetus11.me/reddit/meme",
                    # headers={"Authorization": self.k.villager_api},
                    params={"requesterId": ctx.channel.id},
                )

                meme = cj.classify(await resp.json())

        embed = disnake.Embed(color=self.d.cc, title=meme.title[:256], url=meme.permalink)

        embed.set_footer(text=f"{meme.upvotes}  |  u/{meme.author}", icon_url=self.d.upvote_emoji_image)
        embed.set_image(url=meme.image)

        await ctx.send(embed=embed)

    @commands.command(name="4chan", aliases=["greentext"])
    @commands.cooldown(1, 1.5, commands.BucketType.user)
    async def greentext(self, ctx: Ctx):
        """Sends a greentext from r/greentext"""

        do_nsfw = False

        if isinstance(ctx.channel, disnake.TextChannel):
            do_nsfw = ctx.channel.is_nsfw()

        jj = {"nsfw": True}

        async with SuppressCtxManager(ctx.typing()):
            while (not do_nsfw and jj["nsfw"]) or jj.get("image") is None:
                resp = await self.aiohttp.get(
                    "https://api.iapetus11.me/reddit/greentext",
                    # headers={"Authorization": self.k.villager_api},
                    params={"requesterId": ctx.channel.id},
                )

                jj = await resp.json()

        embed = disnake.Embed(color=self.d.cc)
        embed.set_image(url=jj["image"])

        await ctx.send(embed=embed)

    @commands.command(name="comic")
    @commands.cooldown(1, 1.5, commands.BucketType.user)
    async def comic(self, ctx: Ctx):
        """Sends a comic from r/comics"""

        do_nsfw = False
        if isinstance(ctx.channel, disnake.TextChannel):
            do_nsfw = ctx.channel.is_nsfw()

        comic = {"nsfw": True, "spoiler": True}

        async with SuppressCtxManager(ctx.typing()):
            while comic["spoiler"] or (not do_nsfw and comic["nsfw"]) or comic.get("image") is None:
                resp = await self.aiohttp.get(
                    "https://api.iapetus11.me/reddit/comic",
                    # headers={"Authorization": self.k.villager_api},
                    params={"requesterId": ctx.channel.id},
                )

                comic = cj.classify(await resp.json())

        embed = disnake.Embed(color=self.d.cc, title=comic.title[:256], url=comic.permalink)

        embed.set_footer(text=f"{comic.upvotes}  |  u/{comic.author}", icon_url=self.d.upvote_emoji_image)
        embed.set_image(url=comic.image)

        await ctx.send(embed=embed)

    @commands.command(name="cursed", aliases=["cursedmc"])
    @commands.cooldown(1, 1.5, commands.BucketType.user)
    async def cursed_mc(self, ctx: Ctx):
        if random.choice((True, False)):
            meme = {"nsfw": True, "spoiler": True}

            async with SuppressCtxManager(ctx.typing()):
                while meme["spoiler"] or meme["nsfw"] or meme.get("image") is None:
                    resp = await self.bot.aiohttp.get(
                        "https://api.iapetus11.me/reddit/cursedMinecraft",
                        # headers={"Authorization": self.k.villager_api},
                        params={"requesterId": ctx.channel.id},
                    )

                    meme = cj.classify(await resp.json())

            embed = disnake.Embed(color=self.d.cc, title=meme.title[:256], url=meme.permalink)

            embed.set_footer(text=f"{meme.upvotes}  |  u/{meme.author}", icon_url=self.d.upvote_emoji_image)
            embed.set_image(url=meme.image)

            await ctx.send(embed=embed)
        else:
            embed = disnake.Embed(color=self.d.cc)
            embed.set_image(url=f"https://iapetus11.me/images/cursed_minecraft/{random.choice(self.d.cursed_images)}")

            await ctx.send(embed=embed)

    @commands.command(name="say")
    async def say_text(self, ctx: Ctx, *, text):
        """Sends whatever is put into the command"""

        nice = strip_command(ctx)

        if nice.lower() in INSULTS:
            await ctx.reply("Yes.")
            return

        with suppress(disnake.errors.HTTPException):
            await ctx.message.delete()

        await ctx.send(nice)

    @commands.command(name="villagerspeak")
    async def villager_speak(self, ctx: Ctx, *, msg):
        """Turns the given text into Minecraft villager sounds as text"""

        try:
            translated = self.lang_convert(strip_command(ctx), self.d.fun_langs.villager)
            await ctx.send(translated)
        except ValueError:
            await ctx.send_embed(ctx.l.fun.too_long)

    @commands.command(name="enchant")
    async def enchant_lang(self, ctx: Ctx, *, msg):
        """Turns regular text into the Minecraft enchantment table language"""

        try:
            translated = self.lang_convert((strip_command(ctx)).lower(), self.d.fun_langs.enchant)
            await ctx.send(translated)
        except ValueError:
            await ctx.send_embed(ctx.l.fun.too_long)

    @commands.command(name="unenchant")
    async def unenchant_lang(self, ctx: Ctx, *, msg):
        """Turns the Minecraft enchantment table language back into regular text"""

        try:
            translated = self.lang_convert(strip_command(ctx), self.d.fun_langs.unenchant)
            await ctx.send(translated)
        except ValueError:
            await ctx.send_embed(ctx.l.fun.too_long)

    @commands.command(name="vaporwave")
    async def vaporwave_text(self, ctx: Ctx, *, msg):
        """Turns regular text into vaporwave text"""

        try:
            translated = self.lang_convert(strip_command(ctx), self.d.fun_langs.vaporwave)
            await ctx.send(translated)
        except ValueError:
            await ctx.send_embed(ctx.l.fun.too_long)

    @commands.command(name="sarcastic", aliases=["spongebob"])
    async def sarcastic_text(self, ctx: Ctx, *, msg):
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
    async def clap_cheeks(self, ctx: Ctx, *, text):
        """Puts the :clap: emoji between words"""

        clapped = ":clap: " + " :clap: ".join((strip_command(ctx)).split(" ")) + " :clap:"

        if len(clapped) > 2000:
            await ctx.send_embed(ctx.l.fun.too_long)
            return

        await ctx.send(clapped)

    @commands.command(name="emojify")
    async def emojify(self, ctx: Ctx, *, _text):
        """Turns text or images into emojis"""

        stripped = (strip_command(ctx)).lower()
        text = ""

        for letter in stripped:
            if letter in ALPHABET_LOWER:
                text += f":regional_indicator_{letter}: "
            else:
                text += self.d.emojified.get(letter, letter) + " "

        if len(text) > 2000:
            await ctx.send_embed(ctx.l.fun.too_long)
        else:
            await ctx.send(text)

    @commands.command(name="owo", aliases=["owofy"])
    async def owofy_text(self, ctx: Ctx, *, text):
        """Make any text more cringe"""

        text = text.lower().replace("l", "w").replace("r", "w")

        if len(text) > 1950:
            await ctx.send_embed(ctx.l.fun.too_long)
        else:
            await ctx.send(f"{text} {random.choice(self.d.owos)}")

    @commands.command(name="bubblewrap", aliases=["pop"])
    async def bubblewrap(self, ctx: Ctx, size=None):
        """Sends bubblewrap to the chat"""

        if size is None:
            size = (10, 10)
        else:
            size = size.split("x")

            if len(size) != 2:
                await ctx.send_embed(ctx.l.fun.bubblewrap.invalid_size_1)
                return

            try:
                size[0] = int(size[0])
                size[1] = int(size[1])
            except ValueError:
                await ctx.send_embed(ctx.l.fun.bubblewrap.invalid_size_1)
                return

            for val in size:
                if val < 1 or val > 12:
                    await ctx.send_embed(ctx.l.fun.bubblewrap.invalid_size_2)
                    return

        bubble = "||**pop**||"
        await ctx.send_embed(f"{bubble*size[0]}\n" * size[1])

    @commands.command(name="kill", aliases=["die", "kil", "dorito"])
    async def kill_thing(self, ctx: Ctx, *, thing: typing.Union[disnake.Member, str]):
        if isinstance(thing, disnake.Member):
            thing = thing.mention

        await ctx.send_embed(random.choice(self.d.kills).format(thing[:500], ctx.author.mention))

    @commands.command(name="coinflip", aliases=["flipcoin", "cf"])
    async def coin_flip(self, ctx: Ctx):
        await ctx.send_embed(random.choice(("heads", "tails")))

    @commands.command(name="pat")
    @commands.guild_only()
    async def pat(self, ctx: Ctx, users: commands.Greedy[disnake.Member] = [], *, text: str = ""):
        resp = await self.bot.aiohttp.get("https://rra.ram.moe/i/r?type=pat")
        image_url = "https://rra.ram.moe" + (await resp.json())["path"]

        embed = disnake.Embed(
            color=self.d.cc,
            title=f"**{disnake.utils.escape_markdown(ctx.author.display_name)}** pats {', '.join(f'**{disnake.utils.escape_markdown(u.display_name)}**' for u in users)} {text}"[
                :256
            ],
        )
        embed.set_image(url=image_url)

        await ctx.send(embed=embed)

    @commands.command(name="slap")
    @commands.guild_only()
    async def slap(self, ctx: Ctx, users: commands.Greedy[disnake.Member] = [], *, text: str = ""):
        resp = await self.bot.aiohttp.get("https://rra.ram.moe/i/r?type=slap")
        image_url = "https://rra.ram.moe" + (await resp.json())["path"]

        embed = disnake.Embed(
            color=self.d.cc,
            title=f"**{disnake.utils.escape_markdown(ctx.author.display_name)}** slaps {', '.join(f'**{disnake.utils.escape_markdown(u.display_name)}**' for u in users)} {text}"[
                :256
            ],
        )
        embed.set_image(url=image_url)

        await ctx.send(embed=embed)

    @commands.command(name="achievement", aliases=["mcachieve"])
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def minecraft_achievement(self, ctx: Ctx, *, text):
        url = f"https://api.iapetus11.me/mc/image/achievement/{urlquote(text[:26])}"
        embed = disnake.Embed(color=self.d.cc)

        embed.description = ctx.l.fun.dl_img.format(url)
        embed.set_image(url=url)

        await ctx.send(embed=embed)

    @commands.command(name="splashtext", aliases=["mcsplash", "splashscreen", "splash"])
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def minecraft_splash_screen(self, ctx: Ctx, *, text):
        url = f"https://api.iapetus11.me/mc/image/splash/{urlquote(text[:27])}"
        embed = disnake.Embed(color=self.d.cc)

        embed.description = ctx.l.fun.dl_img.format(url)
        embed.set_image(url=url)

        await ctx.send(embed=embed)

    def calculate_trivia_reward(self, question_difficulty: int) -> int:
        return int((random.random() + 0.25) * (question_difficulty + 0.25) * 9) + 1

    async def trivia_multiple_choice(self, ctx: Ctx, question, do_reward):
        correct_choice = question.a[0]

        choices = question.a.copy()
        random.shuffle(choices)

        embed = disnake.Embed(
            color=self.d.cc,
            title=ctx.l.fun.trivia.title.format(self.d.emojis.bounce, ctx.l.fun.trivia.difficulty[question.d], ":question:"),
        )

        embed.description = "*{}*".format(
            "\n".join(map(" ".join, [question.q.split()[i : i + 7] for i in range(0, len(question.q.split()), 7)]))
        )
        embed.set_footer(text="\uFEFF\n" + ctx.l.fun.trivia.time_to_answer)

        for i, c in enumerate(choices):
            c_column = "\n".join(map(" ".join, [c.split()[i : i + 3] for i in range(0, len(c.split()), 3)]))
            embed.add_field(name="\uFEFF", value=f"**{i+1}.** {c_column}")

            if i % 2 == 0:
                embed.add_field(name="\uFEFF", value="\uFEFF")

        msg = await ctx.reply(embed=embed, mention_author=False)

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
            embed = disnake.Embed(
                color=self.d.cc,
                title=ctx.l.fun.trivia.title_basic.format(self.d.emojis.bounce, ":question:"),
                description=ctx.l.fun.trivia.timeout,
            )
            await msg.edit(embed=embed)
            return
        finally:
            with suppress(disnake.errors.HTTPException):
                await msg.clear_reactions()

        embed = disnake.Embed(
            color=self.d.cc,
            title=ctx.l.fun.trivia.title_basic.format(self.d.emojis.bounce, ":question:"),
        )

        if choices[self.d.emojis.numbers.index(react.emoji) - 1] == correct_choice:
            if do_reward:
                emeralds_won = self.calculate_trivia_reward(question.d)
                await self.db.balance_add(ctx.author.id, emeralds_won)
                correct = random.choice(ctx.l.fun.trivia.correct).format(emeralds_won, self.d.emojis.emerald)
            else:
                correct = random.choice(ctx.l.fun.trivia.correct).split("\n")[0]

            embed.description = correct
        else:
            embed.description = random.choice(ctx.l.fun.trivia.incorrect)

        await msg.edit(embed=embed)

    async def trivia_true_or_false(self, ctx: Ctx, question, do_reward):
        correct_choice = question.a[0]

        embed = disnake.Embed(
            color=self.d.cc,
            title=ctx.l.fun.trivia.title.format(self.d.emojis.bounce, ctx.l.fun.trivia.difficulty[question.d], ":question:"),
        )

        embed.description = "*{}*".format(
            "\n".join(map(" ".join, [question.q.split()[i : i + 7] for i in range(0, len(question.q.split()), 7)]))
        )
        embed.set_footer(text="\uFEFF\n" + ctx.l.fun.trivia.time_to_answer)

        msg = await ctx.reply(embed=embed, mention_author=False)

        await msg.add_reaction(self.d.emojis.yes)
        await msg.add_reaction(self.d.emojis.no)

        def reaction_check(react, r_user):
            return (
                r_user == ctx.author
                and ctx.channel == react.message.channel
                and msg == react.message
                and str(react.emoji) in [self.d.emojis.yes, self.d.emojis.no]
            )

        try:
            react, r_user = await self.bot.wait_for("reaction_add", check=reaction_check, timeout=15)
        except asyncio.TimeoutError:
            embed = disnake.Embed(
                color=self.d.cc,
                title=ctx.l.fun.trivia.title_basic.format(self.d.emojis.bounce, ":question:"),
                description=ctx.l.fun.trivia.timeout,
            )
            await msg.edit(embed=embed)
            return
        finally:
            with suppress(disnake.errors.HTTPException):
                await msg.clear_reactions()

        embed = disnake.Embed(
            color=self.d.cc,
            title=ctx.l.fun.trivia.title_basic.format(self.d.emojis.bounce, ":question:"),
        )

        if (correct_choice == "true" and str(react.emoji) == self.d.emojis.yes) or (
            correct_choice == "false" and str(react.emoji) == self.d.emojis.no
        ):
            if do_reward:
                emeralds_won = self.calculate_trivia_reward(question.d)
                await self.db.balance_add(ctx.author.id, emeralds_won)
                correct = random.choice(ctx.l.fun.trivia.correct).format(emeralds_won, self.d.emojis.emerald)
            else:
                correct = random.choice(ctx.l.fun.trivia.correct).split("\n")[0]

            embed.description = correct
        else:
            embed.description = random.choice(ctx.l.fun.trivia.incorrect)

        await msg.edit(embed=embed)

    @commands.command(name="trivia", aliases=["mctrivia"])
    @commands.guild_only()
    @commands.max_concurrency(1, per=commands.BucketType.user)
    async def minecraft_trivia(self, ctx: Ctx):
        do_reward = (await self.ipc.request({"type": PacketType.TRIVIA, "author": ctx.author.id})).do_reward
        question = random.choice(ctx.l.fun.trivia.questions)

        if question.tf:
            await self.trivia_true_or_false(ctx, question, do_reward)
        else:
            await self.trivia_multiple_choice(ctx, question, do_reward)

    @commands.command(name="gayrate", aliases=["gaypercent"])
    async def gay_rate(self, ctx: Ctx, *, thing: typing.Union[disnake.Member, str] = None):
        if thing is None:
            thing = ctx.author.mention
        elif isinstance(thing, disnake.Member):
            thing = thing.mention

        await ctx.reply_embed(ctx.l.fun.gayrate.format("\uFEFF :rainbow_flag: \uFEFF", thing))


def setup(bot):
    bot.add_cog(Fun(bot))
