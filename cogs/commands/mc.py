from discord.ext import commands
import discord
from mcstatus import MinecraftServer
import socket
from pyraklib.protocol.EncapsulatedPacket import EncapsulatedPacket
from pyraklib.protocol.UNCONNECTED_PING import UNCONNECTED_PING
from pyraklib.protocol.UNCONNECTED_PONG import UNCONNECTED_PONG
import aiohttp
import base64
import json
import asyncio
from random import choice


class Minecraft(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.ses = aiohttp.ClientSession()

        self.g = self.bot.get_cog("Global")

        self.first = ["Hey, you should build", "Hey, what if you made", "Hey, you should build", "What if you built", "What if you made", "You could create", "What if you created", "You could make"]
        self.prenouns = ["a statue of a creeper", "a cozy home with a fireplace", "a secret redstone base", "a statue of Steve", "a command block creation", "a replica of the Statue of Liberty",
                      "a replica of the world", "a statue of Alex", "a statue of Steve & Alex", "a hidden base", "a secret room in your house", "a 2x1 redstone door", "a 2x2 redstone door",
                      "a 2x3 redstone door", "a 3x3 redstone door", "a flying machine", "a working fireplace", "a mansion", "a haunted mansion", "a server lobby", "a golf course", "a pirate ship",
                      "an awesome parkour map", "an adventure map", "a cool statue of your skin", "a realistic model of your house", "pixel art of Pikachu", "pixel art", "a pvp arena",
                      "something, idk", "a recreation of a meme", "an animation with command blocks", "a pvp map", "a dropper map", "a lovely survival world", "a giant hotel",
                      "pixel art of Villager Bot", "pixel art of emeralds", "a giant survival base", "a siege-ready castle", "a castle and lava moat", "a giant tree house", "a giant palace",
                      "a throne fit for a king", "a prison", "pixel art of you", "a statue of a sheep", "a statue of a cow", "a statue of your stuffed animal", "a replica of your pet"
                      "a city block", "an emerald bank", "a fishing hole", "a 3 story tree house", "a cactus farm", "a wheat farm", "a carrot farm", "a floating village", "an auto farm",
                      "a giant farm", "an igloo", "a sky island", "a giant maze", "a toy shop", "a mall", "a swimming pool", "a town hall", "a villager breeding machine", "a tree farm",
                      "an underground garden", "the flag of your home country", "a witch farm", "a giant public library", "a storage room", "a bakery", "a mob arena", "a maze with deadly traps",
                      "a mad science labratory", "a large volcano", "a dog house", "a cat house", "a city park", "a pacman game", "a tnt cannon", "a space ship that can fire tnt", "a giant cake",
                      "a theme park", "a carnival", "a drowned farm", "a blacksmith", "a kelp farm", "a tavern", "a monorail", "a refugee center", "an escape room", "a greenhouse with plants",
                      "a giant slime-block trampoline", "a miniature city", "a satellite dish", "an elven city", "an egyptian pyramid", "a skate park", "a circus", "the Minecraft olympics",
                      "a redstone computer", "your favorite cartoon characters", "an ultra auth-sorting storage system", "a giant tnt cannon", "a player launcher", "a small town", "a bamboo farm",
                      "a farm", "a small hut", "a gaming computer", "an x-wing fighter from Star Wars", "a super-big rainbow with a pot of gold at the end", "giant versions of blocks", "a meatbal",
                      "a computer", "a 20 story apartment building", "a hospital", "a zombie villager curing hospital", "a school", "a viking ship", "a viking village", "some tennis courts",
                      "a massive mine", "a helicopter pad", "a secret FBI base", "a secret CIA base", "Area 51", "a giant sea monster", "a massive cruise ship", "a planet" "the solar system",
                      "a massive abandoned mineshaft", "the kraken", "a seafood resturant", "a resturant that only serves various forms of fried octopus tentacles", "a massive trampoline park",
                      "a statue of a bee", "a giant dragon", "a rainbow-colored dragon", "a hidden enchanting table station", "a redstone drawbridge", "a dump truck", "a dinosaur",
                      "a construction site", "a skyscraper", "an iPhone", "a humble abode", "a river", "a hobbit hole", "a home in a volcano", "a disco", "a creepy campsite", "an awesome jungle"]
        
        self.nouns = ["creeper", "cozy room with a fireplace", "cozy house", "Steve", "Alex", "your skin", "your favorite cartoon character", "pixel art of your Minecraft skin", "Minecraft in Minecraft",
                      "command block creation", "replica of the Statue of Liberty", "replica of the world", "statue of Steve & Alex", "statue of your favorite stuffed animal", "cruise ship",
                      "dinosaur", "bee", "survival base", "castle", "castle with a moat", "blacksmithery", "bakery", "x-wing fighter", "area 51", "redstone drawbridge", "dump truck", "tennis courts",
                      "model of a solar system", "dog house", "villager", "statue of a villager", "giant sea monster", "viking ship", "carrot farm", "player launcher", "tnt cannon", "pacman pixel art",
                      "tree house", "tree farm", "floating village", "town hall", "storage room", "mall", "swimming pool", "monorail", "mansion", "fireplace", "hidden room", "survival world", "hotel",
                      "throne room", "throne for a king", "sky island", "volcano", "hospital", "CIA base", "hobbit hole", "mountain", "river", "winding river", "hydroelectric dam", "power plant",
                      "labratory", "mad science labratory", "skyscraper", "dragon", "resturant", "helicopter pad", "helicopter", "vehicle", "trampoline", "trampoline park", "town", "farm", "PvP arena",
                      "dropper map", "PvE arena", "kraken", "phone", "smart phone", "public library", "secret library", "toy shop", "maze", "winding maze", "underground garden", "emerald bank",
                      "golf course", "tavern", "road", "super-highway", "home", "mob arena", "arena", "city park", "playground", "octopus", "rabbit", "dog", "cat", "sheep", "cow", "camel", "pig",
                      "wandering villager", "villager", "wither", "ender dragon", "statue of a wither", "statue of an ender dragon", "statue of an octopus", "statue of a dog", "palace", "pyramid",
                      "egyptian tomb", "theme park", "computer", "adventure map", "moat", "pirate ship", "cruise-liner", "carrot", "hidden enchanting table station", "skate park", "virus", "camp site",
                      "iPhone", "T.V.", "apartment building", "mineshaft", "gaming computer", "bakery"]
        self.colors = ["red-colored", "orange-colored", "yellow-colored", "green-colored", "blue-colored", "indigo-colored", "violet-colored", "grey", "black", "purple", "white", "brown"]
        self.sizes = ["normal sized", "normally sized", "large", "massive", "huge", "gigantic", "tiny", "small", "microscopic", "normal sized"]

    def cog_unload(self):
        self.bot.loop.create_task(self.stopses())

    async def stopses(self):
        await self.ses.stop()

    @commands.command(name="mcping") # Pings a java edition minecraft server
    async def mcping(self, ctx, *, server: str):
        await ctx.trigger_typing()
        server = server.replace(" ", "")
        if ":" in server:
            s = server.split(":")
            try:
                int(s[1])
            except Exception:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="**"+server+"** is either offline or unavailable at the moment.\n" +
                                                   "Did you type the ip and port correctly? (Like ip:port)\n\nExample: ``"+ctx.prefix+"mcping 172.10.17.177:25565``"))
                return
        if server == "":
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You must specify a server to ping!"))
            return
        status = MinecraftServer.lookup(server)
        try:
            status = status.status()
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=server+" is online with {0} player(s) and a ping of {1} ms.".format(status.players.online, status.latency)))
        except Exception:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="**"+server+"** is either offline or unavailable at the moment.\n" +
                                               "Did you type the ip and port correctly? (Like ip:port)\n\nExample: ``"+ctx.prefix+"mcping 172.10.17.177:25565``"))

    @commands.command(name="mcpeping", aliases=["mcbeping"])
    async def bedrockping(self, ctx, server: str):
        ping = UNCONNECTED_PING()
        ping.pingID = 4201
        ping.encode()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setblocking(0)
        try:
            s.sendto(ping.buffer, (socket.gethostbyname(server), 19132))
            await asyncio.sleep(.75)
            recvData = s.recvfrom(2048)
        except BlockingIOError:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="**"+server+"** is either offline or unavailable at the moment. Did you type the ip correctly?"))
            return
        except socket.gaierror:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="**"+server+"** is either offline or unavailable at the moment. Did you type the ip correctly?"))
            return
        pong = UNCONNECTED_PONG()
        pong.buffer = recvData[0]
        pong.decode()
        sInfo = str(pong.serverName)[2:-2].split(";")
        pCount = sInfo[4]
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=server+" is online with "+pCount+" player(s)."))

    @commands.command(name="stealskin", aliases=["skinsteal", "skin"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def skinner(self, ctx, *, gamertag: str):
        response = await self.ses.get("https://api.mojang.com/users/profiles/minecraft/"+gamertag)
        if response.status == 204:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That player doesn't exist!"))
            return
        uuid = json.loads(await response.text())["id"]
        response = await self.ses.get("https://sessionserver.mojang.com/session/minecraft/profile/"+str(uuid)+"?unsigned=false")
        content = json.loads(await response.text())
        if "error" in content:
            if content["error"] == "TooManyRequestsException":
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Hey! Slow down!"))
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

    @commands.command(name="nametouuid", aliases=["uuid", "getuuid"])
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def getuuid(self, ctx, *, gamertag: str):
        r = await self.ses.post("https://api.mojang.com/profiles/minecraft", json=[gamertag])
        j = json.loads(await r.text()) # [0]['id']
        if j == []:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That user could not be found."))
            return
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"{gamertag}: ``{j[0]['id']}``"))

    @commands.command(name="uuidtoname", aliases=["getgamertag"])
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def getgamertag(self, ctx, *, uuid: str):
        response = await self.ses.get(f"https://api.mojang.com/user/profiles/{uuid}/names")
        if response.status == 204:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That player doesn't exist!"))
            return
        j = json.loads(await response.text())
        name = j[len(j)-1]["name"]
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"{uuid}: ``{name}``"))

    @commands.command(name="mcsales", aliases=["minecraftsales"])
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def mcsales(self, ctx):
        r = await self.ses.post("https://api.mojang.com/orders/statistics", json={"metricKeys": ["item_sold_minecraft", "prepaid_card_redeemed_minecraft"]})
        j = json.loads(await r.text())
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"**{j['total']}** total Minecraft copies sold, **{round(j['saleVelocityPerSeconds'], 3)}** copies sold per second."))

    @commands.command(name="randomserver", aliases=["randommc", "randommcserver", "mcserver", "minecraftserver"])
    async def randommcserver(self, ctx):
        s = choice(self.g.mcServers)
        try:
            online = MinecraftServer.lookup(s['ip']+":"+str(s['port'])).status()
            stat = "<:online:692764696075304960>"
        except Exception:
            stat = "<:offline:692764696431951872>"
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"{stat} \uFEFF ``{s['ip']}:{s['port']}`` {s['version']} ({s['type']})\n{s['note']}"))

    @commands.command(name="buildidea", aliases=["idea"])
    async def buildidea(self, ctx):
        if choice([True, False]):
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"{choice(self.first)} {choice(self.prenouns)}{choice(['!', ''])}"))
        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"{choice(self.first)} a {choice(self.sizes)}, {choice(self.colors)} {choice(self.nouns)}{choice(['!', ''])}"))

def setup(bot):
    bot.add_cog(Minecraft(bot))
