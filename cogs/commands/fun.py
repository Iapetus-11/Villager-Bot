import discord
import asyncio
from discord.ext import commands
from random import choice, randint


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.g = self.bot.get_cog("Global")

    async def lang_convert(self, ctx, msg, lang): # Goes through message and replaces all instances of keys with their values in a dict
        keys = list(lang)
        mes = ""
        for letter in discord.utils.escape_mentions(msg).lower():
            if letter in keys:
                mes += lang[letter]
            else:
                mes += letter
        if len(mes) > 2000:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Uh oh, your message is too long to convert."))
        else:
            await ctx.send(mes)

    @commands.command(name="villagerspeak") # Converts text into villager noises
    async def villager_speak(self, ctx, *, msg):
        await self.lang_convert(ctx, str(msg).replace("\\", "\\\\"), self.g.villagerLang)

    @commands.command(name="enchant") # Text to enchanting table language (Standard Galactic Alphabet)
    async def enchant(self, ctx, *, msg):
        msg = str(msg).replace("```", "").replace("\\", "\\\\")
        await self.lang_convert(ctx, "```" + msg + "```", self.g.enchantLang)

    @commands.command(name="unenchant") # Enchanting table language to text
    async def unenchant(self, ctx, *, msg):
        lang = {}
        for key in list(self.g.enchantLang):
            lang[self.g.enchantLang[key]] = key
        await self.lang_convert(ctx, str(msg), lang)

    @commands.command(name="sarcastic") # Spongebob sarcastic text
    async def sarcasm(self, ctx, *, msg):
        msg = str(msg).replace("\\", "\\\\")
        caps = False
        new = ""
        for letter in msg:
            if caps:
                new += letter.upper()
            else:
                new += letter.lower()
            if not letter == " ":
                caps = not caps
        await ctx.send(new)

    @commands.command(name="say")
    async def say_something(self, ctx, *, text: str):
        await ctx.send(discord.utils.escape_mentions(text))
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="cursed")
    @commands.cooldown(1, 2, commands.BucketType.channel)
    async def cursed_images(self, ctx):
        images = self.g.cursedImages
        cursed = discord.Embed(description="", color=discord.Color.green())
        cursed.set_image(url="http://olimone.ddns.net/images/cursed_minecraft/" + choice(images))
        await ctx.send(embed=cursed)

    @commands.command(name="battle", aliases=["duel", "fight"])
    @commands.cooldown(1, 2, commands.BucketType.channel)
    async def fight(self, ctx, user: discord.User):
        red, gre, blu = (190, 10, 10)
        battleAnnounce = discord.Embed(title="***" + ctx.author.display_name + "***  has challenged ***" + user.display_name + "***  to a sword fight!",
                                       description="**Who will the victor be?**", color=discord.Color.from_rgb(red, gre, blu))
        battleAnnounce.set_thumbnail(url="http://olimone.ddns.net/images/diamondswords2.png")
        await ctx.send(embed=battleAnnounce)
        if ctx.author == user:
            await ctx.send(embed=discord.Embed(color=discord.Color.from_rgb(red, gre, blu), description="**" + user.display_name + "** " + choice(["committed dig straight down.",
                                                                                                                                                   "died by self inflicted stab wound.",
                                                                                                                                                   "died by punching a golem.",
                                                                                                                                                   "dug straight down into lava.",
                                                                                                                                                   "blew themselves up with TNT.",
                                                                                                                                                   "ran into a creeper."])))
            return

        p1_hp = 20
        p2_hp = 20
        await ctx.send(embed=discord.Embed(title="***" + ctx.author.display_name + ":*** " + str(p1_hp) + " hp | ***" + user.display_name + ":*** " + str(p2_hp) + " hp", color=discord.Color.from_rgb(red, gre, blu)))
        while p1_hp > 0 and p2_hp > 0:
            await asyncio.sleep(0.5)
            p2_hp -= randint(2, 12) # Player 1's turn
            p1_hp -= randint(5, 12) # Player 2's turn
            if ctx.author.id == 639498607632056321:
                p2_hp -= 7
            if user.id == 639498607632056321:
                p1_hp -= 7

            if p2_hp < 0:
                p2_hp = 0

            if p1_hp < 0:
                p1_hp = 0

            if p2_hp <= 0:
                p2_hp = 0
                if p1_hp <= 0:
                    p1_hp = 1
                await ctx.send(embed=discord.Embed(title="***" + ctx.author.display_name + ":*** " + str(p1_hp) + " hp | ***" + user.display_name + ":*** " + str(p2_hp) + " hp", color=discord.Color.from_rgb(red, gre, blu)))
                win = discord.Embed(title="**" + ctx.author.display_name + " The Great** has defeated **" + user.display_name + " the lesser!**", color=discord.Color.from_rgb(255, 0, 0))
                win.set_thumbnail(url=str(ctx.author.avatar_url))
                await ctx.send(embed=win)
            elif p1_hp <= 0:
                p1_hp = 0
                if p2_hp <= 0:
                    p2_hp = 1
                await ctx.send(embed=discord.Embed(title="***" + ctx.author.display_name + ":*** " + str(p1_hp) + " hp | ***" + user.display_name + ":*** " + str(p2_hp) + " hp", color=discord.Color.from_rgb(red, gre, blu)))
                win = discord.Embed(title="**" + user.display_name + " The Great** has defeated **" + ctx.author.display_name + " the lesser!**", color=discord.Color.from_rgb(255, 0, 0))
                win.set_thumbnail(url=str(user.avatar_url))
                await ctx.send(embed=win)
            else:
                await ctx.send(embed=discord.Embed(title="***" + ctx.author.display_name + ":*** " + str(p1_hp) + " hp | ***" + user.display_name + ":*** " + str(p2_hp) + " hp", color=discord.Color.from_rgb(255, 0, 0)))

    @commands.command(name="kill", aliases=["murder", "makedie", "killperson", "assasinate"])
    async def kill_person(self, ctx, user: discord.User):
        kill_msgs = ["Wow you suicided {0}.", "You done killed {0}", f"Oh no, {ctx.author.mention} killed "+"{0}", "Wher was u when {0} kil? I on fone, eatin dorito...", "{0} died by deadness", "{0} died by death",
                     "{0} commited dig straight down", "{0} was killed by "+f"{ctx.author.mention}", "{0} died of mysterious causes...", "{0} was killed by choking on a dorito", "{0} done died.", "{0} died a tragic death",
                     "{0} died in a tragic accident involving "+f"{ctx.author.mention}", "{0} suddenly died by dying", f"{ctx.author.mention} has bought a gun,"+" in other news, {0} just died."]
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(kill_msgs).format(user.mention)))

    @commands.command(name="bubblewrap", aliases=["pop"])
    async def bubble_wrap(self, ctx):
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="||pop||||pop||||pop||||pop||||pop||||pop||||pop||||pop||||pop||||pop||\n"*10))

    @commands.command(name="clap")
    async def clap(self, ctx, *, msg):
        await ctx.send(":clap: "+" :clap: ".join(discord.utils.escape_mentions(msg).split(" "))+" :clap:")


def setup(bot):
    bot.add_cog(Fun(bot))
