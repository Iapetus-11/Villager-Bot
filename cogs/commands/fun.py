import discord
import asyncio
from discord.ext import commands
from random import choice, randint


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.g = self.bot.get_cog("Global")

    async def langConvert(self, ctx, msg, lang): # Goes through message and replaces all instances of keys with their values in a dict
        keys = list(lang)
        mes = ""
        for letter in msg.lower():
            if letter in keys:
                mes += lang[letter]
            else:
                mes += letter
        if len(mes) > 2000:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Uh oh, your message is too long to convert."))
        else:
            await ctx.send(mes)

    @commands.command(name="villagerspeak") # Converts text into villager noises
    async def villagerspeak(self, ctx, *, msg):
        await self.langConvert(ctx, str(msg).replace("\\", "\\\\"), self.g.villagerLang)

    @commands.command(name="enchant") # Text to enchanting table language (Standard Galactic Alphabet)
    async def enchant(self, ctx, *, msg):
        msg = str(msg).replace("```", "").replace("\\", "\\\\")
        await self.langConvert(ctx, "```" + msg + "```", self.g.enchantLang)

    @commands.command(name="unenchant") # Enchanting table language to text
    async def unenchant(self, ctx, *, msg):
        lang = {}
        for key in list(self.g.enchantLang):
            lang[self.g.enchantLang[key]] = key
        await self.langConvert(ctx, str(msg), lang)

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
    async def saysomethin(self, ctx, *, text: str):
        embed = discord.Embed(color=discord.Color.green(), description="\uFEFF" + ctx.message.clean_content[len(ctx.message.clean_content)-len(text):])
        embed.set_footer(text=str(ctx.author))
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="cursed")
    @commands.cooldown(1, 1.5, commands.BucketType.channel)
    async def cursedImage(self, ctx):
        images = self.g.cursedImages
        cursed = discord.Embed(description="", color=discord.Color.green())
        cursed.set_image(url="http://172.10.17.177/images/cursed_minecraft/" + choice(images))
        await ctx.send(embed=cursed)

    @commands.command(name="battle", aliases=["duel", "fight"])
    @commands.cooldown(1, 2, commands.BucketType.channel)
    async def fight(self, ctx, user: discord.User):
        red, gre, blu = (190, 10, 10)
        battleAnnounce = discord.Embed(title="***" + ctx.author.display_name + "***  has challenged ***" + user.display_name + "***  to a sword fight!",
                                       description="**Who will the victor be?**", color=discord.Color.from_rgb(red, gre, blu))
        battleAnnounce.set_thumbnail(url="http://172.10.17.177/images/diamondswords2.png")
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


def setup(bot):
    bot.add_cog(Fun(bot))
