from discord.ext import commands
import discord
from random import choice
from mcstatus import MinecraftServer
import arrow
import json
import asyncio
from random import randint, choice
from googlesearch import search
import requests
import base64

class Cmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global startTime
        with open("uptime.txt", "r") as sTime:
            startTime = arrow.get(str(sTime.read()))
        global enchantlang
        with open("enchantlang.json", "r") as langfile:
            enchantlang = json.load(langfile)
        global villagersounds
        with open("villagerlang.json", "r") as villagerlang:
            villagersounds = json.load(villagerlang)
        global cursedImageList
        with open("cursedimages.json", "r") as cursedImages:
            cursedImageList = json.load(cursedImages)["images"]
            
    @commands.command(name="help") #displays help messages
    async def boop(self, ctx):
        msg = ctx.message.clean_content.replace("!!help ", "").replace("!!help", "")
        helpMsg = discord.Embed(
            description = "",
            color = discord.Color.green()
        )
        helpMsg.set_author(name="Villager Bot Commands", url=discord.Embed.Empty, icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
        helpMsg.set_footer(text="Made by Iapetus11#6821")
        if msg == "mc":
            helpMsg.add_field(name="__**Minecraft Stuff**__", value="""
**!!mcping** ***ip:port*** *to check the status of a Java Edition Minecraft server*
**!!stealskin** ***gamertag*** *steal another player's Minecraft skin*""", inline=True)
            await ctx.send(embed=helpMsg)
            return
        
        elif msg == "fun":
            helpMsg.add_field(name="__**Fun Stuff**__", value="""
**!!villagerspeak** ***text*** *turns English text into villager sounds*
**!!enchant** ***text*** *turns english text into the Minecraft enchantment table language, a.k.a. the Standard Galactic Alphabet.*
**!!unenchant** ***text*** *turns the enchanting table language back into English*
**!!battle** ***user*** *allows you to battle your friends!*
**!!cursed** *the bot will upload a cursed Minecraft image*
**!!mine** *go mining with the bot for emeralds*
**!!balance** *the bot will tell you how many emeralds you have*
**!!give** ***@user*** ***amount*** *give mentioned user emeralds*
**!!gamble** ***amount*** *gamble with Villager Bot*
**!!pillage** ***@user*** *attempt to steal emeralds from another person*""", inline=True)
            await ctx.send(embed=helpMsg)
            return
        
        elif msg == "useful":        
            helpMsg.add_field(name="__**Useful/Informative**__", value="""
**!!help** *displays this help message*
**!!info** *displays information about the bot*
**!!ping** *to see the bot's latency between itself and the Discord API*
**!!uptime** *to check how long the bot has been online*
**!!votelink** *to get the link to vote for and support the bot!*
**!!invite** *to get the link to add Villager Bot to your own server!*
**!!say** ***text*** *bot will repeat what you tell it to*
**!!google** ***query*** *bot will search on google for your query*
**!!youtube** ***query*** *bot will search on youtube for your query*
**!!reddit** ***query*** *bot will search on reddit for your query*""", inline=True)
            await ctx.send(embed=helpMsg)
            return
        
        elif msg == "admin":        
            helpMsg.add_field(name="__**Admin Only**__", value="""
**!!purge** ***number of messages*** *deletes n number of messages in the channel it's summoned in*
**!!kick** ***@user*** *kicks the mentioned user*
**!!ban** ***@user*** *bans the mentioned user*
**!!pardon** ***@user*** *unbans the mentioned user*""", inline=True)
            await ctx.send(embed=helpMsg)
            return
        
        else:
            helpMsg.add_field(name="Minecraft", value="``!!help mc``", inline=True)
            helpMsg.add_field(name="Fun", value="``!!help fun``", inline=True)
            helpMsg.add_field(name="Useful", value="``!!help useful``", inline=True)
            helpMsg.add_field(name="\uFEFF", value="\uFEFF", inline=True)
            helpMsg.add_field(name="Admin", value="``!!help admin``", inline=True)
            helpMsg.add_field(name="\uFEFF", value="\uFEFF", inline=True)
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
             color = discord.Color.green()
        )
        infoMsg.add_field(name="Creator", value="Iapetus11#6821", inline=True)
        infoMsg.add_field(name="Bot Library", value="Discord.py", inline=True)
        infoMsg.add_field(name="Command Prefix", value="!!", inline=True)
        infoMsg.add_field(name="Total Servers", value=str(len(self.bot.guilds)), inline=True)
        infoMsg.add_field(name="Shards", value=str(self.bot.shard_count), inline=True)
        infoMsg.add_field(name="Total Users", value=str(len(self.bot.users)), inline=True)
        infoMsg.add_field(name="Bot Page", value="[Click Here](https://top.gg/bot/639498607632056321)", inline=True)
        infoMsg.add_field(name="\uFEFF", value="\uFEFF", inline=True)
        infoMsg.add_field(name="Discord", value="[Click Here](https://discord.gg/39DwwUV)", inline=True)
        infoMsg.set_author(name="Villager Bot Commands", url=discord.Embed.Empty, icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
        await ctx.send(embed=infoMsg)

    @commands.command(name="uptime")
    async def getuptime(self, ctx):
        global startTime
        p = arrow.utcnow()
        diff = (p - startTime)
        days = diff.days
        hours = int(diff.seconds/3600)
        minutes = int(diff.seconds/60)%60
        if days == 1:
            dd = "day"
        else:
            dd = "days"
        if hours == 1:
            hh = "hour"
        else:
            hh = "hours"
        if minutes == 1:
            mm = "minute"
        else:
            mm = "minutes"
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Bot has been online for "+str(days)+" "+dd+", "+str(hours)+" "+hh+", and "+str(minutes)+" "+mm+"!"))

    @commands.command(name="battle", aliases=["duel", "fight", "swordfight"])
    @commands.cooldown(1, 2, commands.BucketType.channel)
    async def fight(self, ctx, user: discord.User):
        red, gre, blu = (190, 10, 10)
        battleAnnounce = discord.Embed(
            title = "***"+ctx.author.display_name+"***  has challenged ***"+user.display_name+"***  to a sword fight!",
            description = "**Who will the victor be?**",
            color = discord.Color.from_rgb(red, gre, blu)
        )
        battleAnnounce.set_thumbnail(url="http://172.10.17.177/images/diamondswords2.png")
        await ctx.send(embed=battleAnnounce)
        if ctx.author == user:
            await ctx.send(embed=discord.Embed(color=discord.Color.from_rgb(red, gre, blu), description="**"+user.display_name+"** "+choice(["committed dig straight down.",
                                                "died by self inflicted stab wound.",
                                                "died by punching a golem.",
                                                "dug straight down into lava.",
                                                "blew themselves up with TNT.",
                                                "ran into a creeper."])))
            return

        p1_hp = 20
        p2_hp = 20
        await ctx.send(embed=discord.Embed(title="***"+ctx.author.display_name+":*** "+str(p1_hp)+" hp | ***"+user.display_name+":*** "+str(p2_hp)+" hp", color = discord.Color.from_rgb(red, gre, blu)))
        while p1_hp > 0 and p2_hp > 0:
            await asyncio.sleep(0.5)
            p2_hp -= randint(1, 12) #player 1's turn
            p1_hp -= randint(4, 12) #player 2's turn
            if ctx.author.id == 639498607632056321 or ctx.author.id == 536986067140608041:
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
                await ctx.send(embed=discord.Embed(title="***"+ctx.author.display_name+":*** "+str(p1_hp)+" hp | ***"+user.display_name+":*** "+str(p2_hp)+" hp", color = discord.Color.from_rgb(red, gre, blu)))
                win = discord.Embed(
                    title = "**"+ctx.author.display_name+" The Great** has defeated **"+user.display_name+" the lesser!**",
                    color = discord.Color.from_rgb(255, 0, 0)
                )
                win.set_thumbnail(url=str(ctx.author.avatar_url))
                await ctx.send(embed=win)
            elif p1_hp <= 0:
                p1_hp = 0
                if p2_hp <= 0:
                    p2_hp = 1
                await ctx.send(embed=discord.Embed(title="***"+ctx.author.display_name+":*** "+str(p1_hp)+" hp | ***"+user.display_name+":*** "+str(p2_hp)+" hp", color = discord.Color.from_rgb(red, gre, blu)))
                win = discord.Embed(
                    title = "**"+user.display_name+" The Great** has defeated **"+ctx.author.display_name+" the lesser!**",
                    color = discord.Color.from_rgb(255, 0, 0)
                )
                win.set_thumbnail(url=str(user.avatar_url))
                await ctx.send(embed=win)
            else:
                await ctx.send(embed=discord.Embed(title="***"+ctx.author.display_name+":*** "+str(p1_hp)+" hp | ***"+user.display_name+":*** "+str(p2_hp)+" hp", color = discord.Color.from_rgb(255, 0, 0)))
            
    @commands.command(name="cursed")
    @commands.cooldown(1, 1, commands.BucketType.channel)
    async def cursedImage(self, ctx):
        global cursedImageList
        
        cursed = discord.Embed(
            description = "",
            color = discord.Color.green()
        )
        
        cursedImage = choice(cursedImageList)
        cursed.set_image(url="http://172.10.17.177/images/cursed_minecraft/"+cursedImage)
        await ctx.send(embed=cursed)
        
    @commands.command(name="vote", aliases=["votelink"])
    async def votelink(self, ctx):
        voteL = discord.Embed(
             title = "Vote for Villager Bot",
             description = "[Click Here!](https://top.gg/bot/639498607632056321/vote)",
             url = "https://top.gg/bot/639498607632056321/vote",
             color = discord.Color.green()
        )
        voteL.set_thumbnail(url="http://172.10.17.177/images/villagerbotsplash1.png")
        await ctx.send(embed=voteL)
    
    @commands.command(name="invite", aliases=["invitelink"])
    async def inviteLink(self, ctx):
        invL = discord.Embed(
             title = "Add Villager Bot to your server",
             description = "[Click Here!](https://discordapp.com/api/oauth2/authorize?client_id=639498607632056321&permissions=8&scope=bot)",
             url = "https://discordapp.com/api/oauth2/authorize?client_id=639498607632056321&permissions=8&scope=bot",
             color = discord.Color.green()
        )
        invL.set_thumbnail(url="http://172.10.17.177/images/villagerbotsplash1.png")
        await ctx.send(embed=invL)
        
    @commands.command(name="say")
    async def saysomethin(self, ctx):
        if ctx.message.clean_content.replace("!!say", "").replace("@", "") == "":
            return
        await ctx.send(ctx.message.clean_content.replace("!!say", "").replace("@", ""))
        try:
            await ctx.message.delete()
        except Exception:
            pass
        
    @commands.command(name="google")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def googleSearch(self, ctx):
        query = ctx.message.clean_content.replace("!!google", "")
        if query == "":
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have to actually tell me what to search for, idiot."))
            return
        await ctx.trigger_typing()
        for result in search(query, tld="co.in", num=1, stop=1, pause=0):
            await ctx.send(result)
        
    @commands.command(name="youtube")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def ytSearch(self, ctx):
        query = ctx.message.clean_content.replace("!!youtube", "")
        if query == "":
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have to actually tell me what to search for, idiot."))
            return
        await ctx.trigger_typing()
        for result in search(query, tld="co.in", domains=["youtube.com"], num=1, stop=1, pause=0):
            await ctx.send(result)
        
    @commands.command(name="reddit")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def redditSearch(self, ctx):
        query = ctx.message.clean_content.replace("!!reddit", "")
        if query == "":
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have to actually tell me what to search for, idiot."))
            return
        await ctx.trigger_typing()
        for result in search(query, tld="co.in", domains=["reddit.com"], num=1, stop=1, pause=0):
            await ctx.send(result)
            
    @commands.command(name="stealskin", aliases=["skinsteal", "skin"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def skinner(self, ctx, *, gamertag: str):
        response = requests.get("https://api.mojang.com/users/profiles/minecraft/"+gamertag)
        if response.status_code == 204:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Profile not found!"))
            return
        uuid = json.loads(response.content)["id"]
        response = requests.get("https://sessionserver.mojang.com/session/minecraft/profile/"+uuid+"?unsigned=false")
        content = json.loads(response.content)
        if "error" in content:
            if content["error"] == "TooManyRequestsException":
                await ctx.send(embed=discord.Embed(color=discord.Color.green(),
                                                   description="Stop sending so many requests! Try again in a minute!"))
                return
        undec = base64.b64decode(content["properties"][0]["value"])
        try:
            url = json.loads(undec)["textures"]["SKIN"]["url"]
        except Exception:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="An error occurred while fetching that skin!"))
            return
        skinEmbed = discord.Embed(color=discord.Color.green(), description=gamertag+"'s skin\n[**[Download]**]("+url+")")
        skinEmbed.set_thumbnail(url=url)
        skinEmbed.set_image(url="https://mc-heads.net/body/"+gamertag)
        await ctx.send(embed=skinEmbed)
    
def setup(bot):
    bot.add_cog(Cmds(bot))
