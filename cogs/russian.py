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

    @commands.command(name="помощь") #displays help messages
    async def help(self, ctx):
        helpMsg = discord.Embed(
            description = "",
            color = discord.Color.blue()
        )
        helpMsg.set_thumbnail(url="http://172.10.17.177/images/villagerbotsplash1.png")
        helpMsg.add_field(name="__**Полезные команды**__", value="""
**!!инфо** *отображает информациюо боте*
**!!пинг** *отображает задержку между ботом и дискордом*
**!!мкпинг** ***айпи:порт*** *проверяет статус сервера (Джава Едишен)*
**!!аптайм** *проверяет когда бот был в сети в посленее время*
**!!админпомощь** *увидеть команды для админа (Права админа необходимы)*
**!!голосовать** *получить ссылку для голосования за бота!*
""")
        helpMsg.add_field(name="__**Фан команды**__", value="""
**!!жительскажи** ***текст*** *превращает Английский текст в звуки жителя*
**!!зачаровать** ***текст*** *превращает Английский текст в язык зачаровательного стола, тоесть Стандартный Галактичейский Алфавит.*
**!!разчаровать** ***текст*** *превращает язык зачаровательного стола обратно в Английский*
**!!баттл** ***пользователь*** *позволяет сразиться с другом!*
**!!проклятыймайнкрафт** *бот отправляйет изображения проклятого майнкрафта*
    """)
        helpMsg.add_field(name="__**Нужно больще помощи?**__", value="""Проверь
оффициальный дискорд сервер Жителя бота здесь: https://discord.gg/39DwwUV""")
        await ctx.send(embed=helpMsg)

    @commands.command(name="мкпинг") #pings a java edition minecraft server
    async def mcping(self, ctx):
        await ctx.trigger_typing()
        server = ctx.message.clean_content.replace("!!мкпинг", "").replace(" ", "")
        if server == "":
            await ctx.send("Ты должен написать айпи сервера!")
            return
        status = MinecraftServer.lookup(server)
        try:
            status = status.status()
            await ctx.send(server+" его онлайн {0} игрока(ов) и пинг сервера {1} ms.".format(status.players.online, status.latency))
        except Exception:
            await ctx.send(server+" сервер не доступен или не отвечает в этот момент.")
            await ctx.send("Вы проверили айпи и порт сервера? (например: айпи:порт)")

    @commands.command(name="пинг", aliases=["задержка"]) #checks latency between Discord API and the bot
    async def ping(self, ctx):
        await ctx.send("Понг! "+str(self.bot.latency*1000)[:5]+" ms")

    @commands.command(name="жительскажи") #converts english into villager noises
    async def villagerspeak(self, ctx):
        global villagersounds
        text = ctx.message.clean_content.replace("!!жительскажи", "")
        if text == "":
            await ctx.send("Ты должен отправить текст чтобы я его превратил звуки жителя!")
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
            await ctx.send("Сообщение слишком длинное.")

    @commands.command(name="зачаровать") #converts english to enchantment table language
    async def enchant(self, ctx):
        global enchantlang
        msg = ctx.message.clean_content.replace("!!зачаровать", "")
        if msg == "":
            await ctx.send("Ты должен отправить текст чтобы я его превратил в язык стола зачарования !")
            return
        for key, value in enchantlang.items():
            msg = msg.replace(key, value)
        if len(msg)+6 <= 2000:
            await ctx.send("```"+msg+"```")
        else:
            await ctx.send("Сообщение слишком длинное.")

    @commands.command(name="разчаровать") #converts enchantment table language to english
    async def unenchant(self, ctx):
        global enchantlang
        msg = ctx.message.clean_content.replace("!!разчаровать", "")
        if msg == "":
            await ctx.send("Ты должен написать сообщение чтобы я понял что написано на английском!")
            return
        for key, value in enchantlang.items():
            msg = msg.replace(value, key)
        if len(msg) <= 2000:
            await ctx.send(msg.lower())
        else:
            await ctx.send("Сообщение очень длинное.")

    @commands.command(name="инфо", aliases=["информация"])
    async def information(self, ctx):
        infoMsg = discord.Embed(
            description = "",
            color = discord.Color.blue()
        )
        infoMsg.set_thumbnail(url="http://172.10.17.177/images/villagerbotsplash1.png")
        infoMsg.add_field(name="__**Житель бот**__", value="""
Запрагроммирован: **Iapetus11#6821**
Всего пользователей: {1}
Всего серверов: {0}
Страница бота: https://top.gg/bot/639498607632056321
Оффициальный дискорд сервер: https://discord.gg/39DwwUV\n""".format(str(len(self.bot.guilds)), str(len(self.bot.users))))
        await ctx.send(embed=infoMsg)

    @commands.command(name="аптайм")
    async def getuptime(self, ctx):
        global startTime
        with open("uptime.txt", "r") as f:
            startTime = arrow.get(str(f.read()))
        await ctx.send("Бот был в онлайне "+startTime.humanize()+"!")

    @commands.command(name="баттл", aliases=["дуель", "драться", "схваткасмечом"])
    async def fight(self, ctx, user: discord.User):
        battleAnnounce = discord.Embed(
            title = "***"+ctx.message.author.display_name+"***  вызвал  ***"+user.display_name+"***  на дуэль!",
            description = "**Кто победит?**",
            color = discord.Color.from_rgb(255, 0, 0)
        )
        battleAnnounce.set_thumbnail(url="http://172.10.17.177/images/diamondswords2.png")
        await ctx.send(embed=battleAnnounce)
        if ctx.message.author == user:
            await ctx.send("**"+user.display_name+"** "+choice(["нарушил первое правило майнкрафта.",
                                                "задохнулся в сетене.",
                                                "умер ударами голема.",
                                                "копался под себя и упал в лаву.",
                                                "взорвал себя с помощью ТНТ.",
                                                "взорвался крипером."]))
            return

        p1_hp = 20
        p2_hp = 20
        await ctx.send(embed=discord.Embed(title="***"+ctx.message.author.display_name+":*** "+str(p1_hp)+" хп | ***"+user.display_name+":*** "+str(p2_hp)+" хп", color = discord.Color.from_rgb(255, 0, 0)))
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
                await ctx.send(embed=discord.Embed(title="***"+ctx.message.author.display_name+":*** "+str(p1_hp)+" хп | ***"+user.display_name+":*** "+str(p2_hp)+" хп", color = discord.Color.from_rgb(255, 0, 0)))
                win = discord.Embed(
                    title = "**"+ctx.message.author.display_name+" Победитель** победил **"+user.display_name+" лузера!**",
                    color = discord.Color.from_rgb(255, 0, 0)
                )
                win.set_thumbnail(url=str(ctx.message.author.avatar_url))
                await ctx.send(embed=win)
            elif p1_hp <= 0:
                p1_hp = 0
                if p2_hp <= 0:
                    p2_hp = 1
                await ctx.send(embed=discord.Embed(title="***"+ctx.message.author.display_name+":*** "+str(p1_hp)+" хп | ***"+user.display_name+":*** "+str(p2_hp)+" хп", color = discord.Color.from_rgb(255, 0, 0)))
                win = discord.Embed(
                    title = "**"+user.display_name+" Победитель** победил **"+ctx.message.author.display_name+" лузера!**",
                    color = discord.Color.from_rgb(255, 0, 0)
                )
                win.set_thumbnail(url=str(user.avatar_url))
                await ctx.send(embed=win)
            else:
                await ctx.send(embed=discord.Embed(title="***"+ctx.message.author.display_name+":*** "+str(p1_hp)+" хп | ***"+user.display_name+":*** "+str(p2_hp)+" хп", color = discord.Color.from_rgb(255, 0, 0)))
            
    @commands.command(name="проклятыймайнкрафт")
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
            color = discord.Color.blue()
        )
        
        cursedImage = choice(imageList)
        cursed.set_image(url="http://172.10.17.177/images/cursed_minecraft/"+cursedImage)
        await ctx.send(embed=cursed)
        
    @commands.command(name="голосовать", aliases=["ссылкадляголосования"])
    async def votelink(self, ctx):
        voteL = discord.Embed(
             title = "Голосуй за Житель бот",
             url = "https://top.gg/bot/639498607632056321/vote",
             footer = "click this link ^",
             color = discord.Color.blue()
        )
        voteL.set_footer(text="Нажми на ссылку ниже!")
        await ctx.send(embed=voteL)
        
    @commands.command(name="админпомощь", aliases=["админкоманды", "помощьадмина"])
    @commands.has_permissions(administrator=True)
    async def adminCommands(self, ctx):
        helpMsg = discord.Embed(
            description = "",
            color = discord.Color.blue()
        )
        helpMsg.add_field(name="__Помощь по администрации сервера__", value="""
**!!очистить** ***число сообщений*** *удаляет указанное число сообщений*
**!!кик** ***@пользователь*** *кикает указаного пользователя*
**!!бан** ***@пользователь*** *банит указаного пользователя*
**!!разбан** ***@пользователь*** *разбанивает указаного пользователя*
    """)
        await ctx.send(embed=helpMsg)

    @commands.command(name="очистить")
    @commands.has_permissions(administrator=True)
    async def purgeMessages(self, ctx, *, message: str):
        try:
            n = int(message)
        except Exception:
            await ctx.send("Это не целое число!")
        else:
            await ctx.channel.purge(limit=n+1)
            
    @commands.command(name="бан")
    @commands.has_permissions(administrator=True)
    async def banUser(self, ctx, *, user: discord.User):
        try:
            await ctx.guild.ban(user)
        except discord.Forbidden:
            await ctx.send("Бот не имеет администрационых прав.")

    @commands.command(name="разбан")
    @commands.has_permissions(administrator=True)
    async def pardonUser(self, ctx, *, user: discord.User):
        try:
            await ctx.guild.unban(user)
        except discord.Forbidden:
            await ctx.send("Bot does not have proper permissions.")
        except discord.HTTPException:
            await ctx.send("Произошла ошибка с разбаном.")

    @commands.command(name="кик")
    @commands.has_permissions(administrator=True)
    async def kickUser(self, ctx, *, user: discord.User):
        try:
            await ctx.guild.kick(user)
        except discord.Forbidden:
            await ctx.send("Бот не имеет администрационых прав")
    
def setup(bot):
    bot.add_cog(Cmds(bot))

