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

class Minecraft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ses = aiohttp.ClientSession()
        
    def cog_unload(self):
        self.bot.loop.create_task(self.stopses())
        
    async def stopses(self):
        await self.ses.stop()
        
    @commands.command(name="mcping") #pings a java edition minecraft server
    async def mcping(self, ctx):
        await ctx.trigger_typing()
        server = ctx.message.clean_content.replace(ctx.prefix+"mcping", "").replace(" ", "")
        if ":" in server:
            s = server.split(":")
            try:
                int(s[1])
            except Exception:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="**"+server+"** is either offline or unavailable at the moment.\n"+
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
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="**"+server+"** is either offline or unavailable at the moment.\n"+
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
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Profile not found!"))
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
        
    @commands.command(name="getuuid")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def getuuid(self, ctx, *, gamertag: str):
        r = await self.ses.post("https://api.mojang.com/profiles/minecraft", json=[gamertag])
        j = json.loads(await r.text()) #[0]['id']
        if j == []:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That user could not be found."))
            return
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"{gamertag}: ``{j[0]['id']}``"))
        
def setup(bot):
    bot.add_cog(Minecraft(bot))