from discord.ext import commands
import discord
from random import choice
from mcstatus import MinecraftServer
import arrow
import json
import asyncio
from random import randint, choice

#other
global startTime
global enchantlang
with open("enchantlang.json", "r") as langfile:
    enchantlang = json.load(langfile)
global villagersounds
with open("villagerlang.json", "r") as villagerlang:
    villagersounds = json.load(villagerlang)

class Cmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help") #displays help messages
    async def help(self, ctx):
        helpMsg = discord.Embed(
            description = "",
            color = discord.Color.green()
        )
        helpMsg.set_thumbnail(url="http://172.10.17.177/images/villagerbotsplash1.png")
        helpMsg.add_field(name="__**Fun Commands**__", value="""
**!!villagerspeak** ***text*** *turns English text into villager sounds*
**!!enchant** ***text*** *turns english text into the Minecraft enchantment table language, a.k.a. the Standard Galactic Alphabet.*
**!!unenchant** ***text*** *turns the enchanting table language back into English*
**!!battle** ***user*** *allows you to battle your friends!*
**!!cursed** *the bot will upload a cursed Minecraft image*
**!!mine** *go mining with the bot for emeralds*
**!!balance** *the bot will tell you how many emeralds you have*
**!!give** ***@user*** ***amount*** *give mentioned user emeralds*
**!!gamble** ***amount*** *gamble with Villager Bot*
\uFEFF""", inline=True)
        
        helpMsg.add_field(name="__**Useful Commands**__", value="""
**!!info** *displays information about the bot*
**!!ping** *to see the bot's latency between itself and the Discord API*
**!!mcping** ***ip:port*** *to check the status of a Java Edition Minecraft server*
**!!uptime** *to check how long the bot has been online*
**!!adminhelp** *to see the admin commands (admin perms required for use)*
**!!votelink** *to get the link to vote for and support the bot!*
**!!invite** *to get the link to add Villager Bot to your own server!*
**!!say** ***text*** *bot will repeat what you tell it to*
\uFEFF""", inline=True)
        helpMsg.add_field(name="\uFEFF", value="""Need more help? Check out the Villager Bot [Support Server](https://discord.gg/39DwwUV)
Enjoying the bot? Vote for us on [top.gg](https://top.gg/bot/639498607632056321/vote)""", inline=False)
        await ctx.send(embed=helpMsg)

    @commands.command(name="mcping") #pings a java edition minecraft server
    async def mcping(self, ctx):
        await ctx.trigger_typing()
        server = ctx.message.clean_content.replace("!!mcping", "").replace(" ", "")
        if server == "":
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You must specify a server to ping!"))
            return
        status = MinecraftServer.lookup(server)
        try:
            status = status.status()
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=server+" is online with {0} player(s) and a ping of {1} ms.".format(status.players.online, status.latency)))
        except Exception:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=server+" is either offline or unavailable at the moment.\nDid you type the ip and port correctly? (Like ip:port)"))

    @commands.command(name="ping", aliases=["latency"]) #checks latency between Discord API and the bot
    async def ping(self, ctx):
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Pong! "+str(round(self.bot.latency*1000, 2))+" ms"))

    @commands.command(name="villagerspeak") #converts english into villager noises
    async def villagerspeak(self, ctx):
        global villagersounds
        text = ctx.message.clean_content.replace("!!villagerspeak", "")
        if text == "":
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You must send text for the bot to turn in to villager sounds!"))
            return
        villager = ""
        letters = list(text)
        for letter in letters:
            if letter.lower() in villagersounds:
                villager += villagersounds.get(letter.lower())
            else:
                villager += letter.lower()
        if not len(villager) > 2000:
            await ctx.send(villager)
        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Message would be too long to convert."))

    @commands.command(name="enchant") #converts english to enchantment table language
    async def enchant(self, ctx):
        global enchantlang
        msg = ctx.message.clean_content.replace("!!enchant", "")
        if msg == "":
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You must send text for the bot to turn into the enchantment table language!"))
            return
        for key, value in enchantlang.items():
            msg = msg.replace(key, value)
        if len(msg)+6 <= 2000:
            await ctx.send("```"+msg+"```")
        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Message would be too long to convert."))

    @commands.command(name="unenchant") #converts enchantment table language to english
    async def unenchant(self, ctx):
        global enchantlang
        msg = ctx.message.clean_content.replace("!!unenchant", "")
        if msg == "":
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You must send text for the bot to turn back into English!"))
            return
        for key, value in enchantlang.items():
            msg = msg.replace(value, key)
        if len(msg) <= 2000:
            await ctx.send(msg.lower())
        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Message would be too long to convert."))

    @commands.command(name="info", aliases=["information"])
    async def information(self, ctx):
        infoMsg = discord.Embed(
            description = "",
            color = discord.Color.green()
        )
        infoMsg.set_thumbnail(url="http://172.10.17.177/images/villagerbotsplash1.png")
        infoMsg.add_field(name="__**Villager Bot**__", value="""
Programmed By: **Iapetus11#6821**
Bot Library: discord.py
Total Users: {1}
Total Servers: {0}
Bot Page: [top.gg/bot/639498607632056321](https://top.gg/bot/639498607632056321)
Public Discord: [discord.gg/39dwwUV](https://discord.gg/39DwwUV)\n""".format(str(len(self.bot.guilds)), str(len(self.bot.users))))
        infoMsg.set_footer(text="Vote for us on top.gg!")
        await ctx.send(embed=infoMsg)

    @commands.command(name="uptime")
    async def getuptime(self, ctx):
        global startTime
        with open("uptime.txt", "r") as f:
            startTime = arrow.get(str(f.read()))
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Bot has been online since "+startTime.humanize()+"!"))

    @commands.command(name="battle", aliases=["duel", "fight", "swordfight"])
    async def fight(self, ctx, user: discord.User):
        battleAnnounce = discord.Embed(
            title = "***"+ctx.message.author.display_name+"***  has challenged ***"+user.display_name+"***  to a sword fight!",
            description = "**Who will the victor be?**",
            color = discord.Color.from_rgb(250, 10, 10)
        )
        battleAnnounce.set_thumbnail(url="http://172.10.17.177/images/diamondswords2.png")
        await ctx.send(embed=battleAnnounce)
        if ctx.message.author == user:
            await ctx.send(embed=discord.Embed(color=discord.Color.from_rgb(250, 10, 10), description="**"+user.display_name+"** "+choice(["committed dig straight down.",
                                                "died by self inflicted stab wound.",
                                                "died by punching a golem.",
                                                "dug straight down into lava.",
                                                "blew themselves up with TNT.",
                                                "ran into a creeper."])))
            return

        p1_hp = 20
        p2_hp = 20
        await ctx.send(embed=discord.Embed(title="***"+ctx.message.author.display_name+":*** "+str(p1_hp)+" hp | ***"+user.display_name+":*** "+str(p2_hp)+" hp", color = discord.Color.from_rgb(250, 10, 10)))
        while p1_hp > 0 and p2_hp > 0:
            await asyncio.sleep(0.5)
            p2_hp -= randint(1, 12) #player 1's turn
            p1_hp -= randint(4, 12) #player 2's turn
            if ctx.message.author.id == 639498607632056321 or ctx.message.author.id == 536986067140608041:
                p2_hp -= 7
            if user.id == 639498607632056321 or user.id == 536986067140608041:
                p1_hp -= 7
                
            if p2_hp < 0:
                p2_hp = 0

            if p1_hp < 0:
                p1_hp = 0
            
            if p2_hp <= 0:
                p2_hp = 0
                if p1_hp <= 0:
                    p1_hp = 1
                await ctx.send(embed=discord.Embed(title="***"+ctx.message.author.display_name+":*** "+str(p1_hp)+" hp | ***"+user.display_name+":*** "+str(p2_hp)+" hp", color = discord.Color.from_rgb(250, 10, 10)))
                win = discord.Embed(
                    title = "**"+ctx.message.author.display_name+" The Great** has defeated **"+user.display_name+" the lesser!**",
                    color = discord.Color.from_rgb(255, 0, 0)
                )
                win.set_thumbnail(url=str(ctx.message.author.avatar_url))
                await ctx.send(embed=win)
            elif p1_hp <= 0:
                p1_hp = 0
                if p2_hp <= 0:
                    p2_hp = 1
                await ctx.send(embed=discord.Embed(title="***"+ctx.message.author.display_name+":*** "+str(p1_hp)+" hp | ***"+user.display_name+":*** "+str(p2_hp)+" hp", color = discord.Color.from_rgb(250, 10, 10)))
                win = discord.Embed(
                    title = "**"+user.display_name+" The Great** has defeated **"+ctx.message.author.display_name+" the lesser!**",
                    color = discord.Color.from_rgb(255, 0, 0)
                )
                win.set_thumbnail(url=str(user.avatar_url))
                await ctx.send(embed=win)
            else:
                await ctx.send(embed=discord.Embed(title="***"+ctx.message.author.display_name+":*** "+str(p1_hp)+" hp | ***"+user.display_name+":*** "+str(p2_hp)+" hp", color = discord.Color.from_rgb(255, 0, 0)))
            
    @commands.command(name="cursed")
    async def cursedImage(self, ctx):
        imageList = ["airr.png", "alexaandstevena.jpg", "animals.png", "armedanddangerouscreeper.png",
                    "asmallgraphicalerror.png", "barrelchest.jpg", "beans.jpg", "beewither.jpg", "bootsword.png",
                    "brokenvillagers.jpg", "buffsteve.png", "buffsteve2.png", "burntchickennugget.jpg",
                    "censored1.jpg", "chaftingfurnset.png", "chair.png", "chest1.png", "chester.jpg",
                    "chestman.jpg", "chestnugget.jpg", "circularcreeper.png", "circularportal.jpg",
                    "coalaxe.jpg", "cow.jpg", "creeperbees.jpg", "creeperwithfeet.png", "creepigandpigger.jpg",
                    "crispysteve.jpg", "cursedredstone.jpg", "cursedstairs.png", "cursedsteves.jpg",
                    "diagonalgrass.png", "diagonalpiston.jpg", "diagonalportal.jpg", "diamondcrafting.png",
                    "diamondcreeper.jpg", "diamondnugget.jpg", "diamondpickaxe.png", "dirtmonds.jpg",
                    "doubelfurnace.jpg", "doubleenderchest.jpg", "doublerailchest.jpg",
                    "enchantingtablebutnobooks.png", "enderchestportal.jpg", "endermaninwater.jpg",
                    "entherportal.jpg", "expensivedirthouse.png", "expensivegrass.png", "f.png",
                    "firebutonwater.png", "flipphoneminecraft.jpg", "gamergirlbathwater.jpg",
                    "gianthulkzombiesteve.png", "giantmutantcreeper.png", "gtacraft.jpg",
                    "halfslabofdirt.png", "heqq.png", "illegalshape.jpg", "inveretedportal.png",
                    "invertedfencesandwalls.png", "inverted_furnace.jpg", "ironwoodenpick.jpg",
                    "lavawaterslabs.png", "longboichest.jpg", "longfurnace.jpg", "longhoe.jpg", "longpiston.jpg",
                    "manypickaxe.jpg", "minedlava.jpg", "mineladder.jpg", "minepig.jpg", "morecursedstairs.jpg",
                    "multiboss.png", "multipiston.png", "multishotfishingrod.png", "nethershortal.png",
                    "oakwoodingot.jpg", "pandas.jpg", "perfectlybalancedasallthingsshouldbe.png",
                    "pickaxewooden.png", "pignig.jpg", "pistonnotsip.png", "porkchopwood.jpg",
                    "rainingtorches.jpg", "realisticlivestock.jpg", "redstone.jpg", "redstonewither.png",
                    "ricardogolem.png", "rippedsteve.png", "roundmc.png", "roundsteve.png", "sandcoalore.png",
                    "scaredvillager.png", "sexysteve.jpg", "sidewaysbed.jpg", "sidewayschest.jpg",
                    "sidewayschest2.jpg", "slabs.png", "smallboichest.jpg", "spidercreep.jpg", "spooktober.jpg",
                    "stairchest.jpg", "stevebutapig.jpg", "stevedragon.png", "stevesteve.png", "stevetposing.jpg",
                    "stevewithfingers.png", "stevewithfingers2.jpg", "stoneore.png", "suicidalsteve.jpg",
                    "svillager.png", "tallchest.jpg", "tallvillager.png", "teslacraft.jpg", "thiccboichest.jpg",
                    "thiccsteve2.png", "thing.py", "triangularcraftingtable.jpg", "underwaterenderman.png",
                    "verticalminecart.jpg", "verticalredstone.png", "villader.png", "villagerghast.jpg",
                    "villagerup.png", "watermelooon.png", "wava.png", "winniethepooandtrump.jpg", "xwingcraft.jpg",
                    "angrychest.jpg", "brazzers.JPG", "cacti.jpg", "chestdir.jpg", "chonker.jpg", "chonker2.png",
                    "emeraldingot.jpg", "fatherobrine.gif", "gardens.jpg", "halftnt.jpg", "longpiston3.jpg",
                    "piggo.jpg", "pool.jpg", "squiddyvillager.jpg", "stevebutacow.jpg", "stevehd.jpg", "tinysteve.jpg",
                    "4dimensionalbed.png", "angrydoggo.jpg", "beaconballs.png", "pistonblock22.png", "roundlog.png",
                    "shep420.gif"]
        
        cursed = discord.Embed(
            description = "",
            color = discord.Color.green()
        )
        
        cursedImage = choice(imageList)
        cursed.set_image(url="http://172.10.17.177/images/cursed_minecraft/"+cursedImage)
        await ctx.send(embed=cursed)
        
    @commands.command(name="votelink", aliases=["vote"])
    async def votelink(self, ctx):
        voteL = discord.Embed(
             title = "Vote for Villager Bot",
             description = "Click the link above!",
             url = "https://top.gg/bot/639498607632056321/vote",
             color = discord.Color.green()
        )
        voteL.set_thumbnail(url="http://172.10.17.177/images/villagerbotsplash1.png")
        await ctx.send(embed=voteL)
    
    @commands.command(name="invite", aliases=["invitelink"])
    async def inviteLink(self, ctx):
        invL = discord.Embed(
             title = "Add Villager Bot to your server",
             description = "Click the link above!",
             url = "https://top.gg/bot/639498607632056321/invite",
             color = discord.Color.green()
        )
        invL.set_thumbnail(url="http://172.10.17.177/images/villagerbotsplash1.png")
        await ctx.send(embed=invL)
        
    @commands.command(name="say")
    async def saysomethin(self, ctx):
        await ctx.send(ctx.message.clean_content.replace("!!say", "").replace("@", ""))
        try:
            await ctx.message.delete()
        except Exception:
            pass
    
def setup(bot):
    bot.add_cog(Cmds(bot))
