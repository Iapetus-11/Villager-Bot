from discord.ext import commands
import discord
import socket
from pyraklib.protocol.EncapsulatedPacket import EncapsulatedPacket
from pyraklib.protocol.UNCONNECTED_PING import UNCONNECTED_PING
from pyraklib.protocol.UNCONNECTED_PONG import UNCONNECTED_PONG
from mcstatus import MinecraftServer
import asyncio

class Xenon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_message(self, message):
        if "discord.gg" in message.content:
            if message.channel.guild.id == 593954944059572235:
                if message.channel.id in [593954944059572237, 593962666695983106, 609104954224803844, 594014175265685532, 659542937285165056, 636324104055816193]:
                    try:
                        await message.delete()
                        await message.channel.send(embed=discord.Embed(color=discord.Color.green(), description="Discord server links aren't allowed here!"))
                    except Exception:
                        pass
    
    @commands.command(name="mcstatus")
    async def mcstatus(self, ctx):
        await ctx.trigger_typing()
        ping = UNCONNECTED_PING()
        ping.pingID = 4201
        ping.encode()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setblocking(0)
        try:
            s.sendto(ping.buffer, ("172.10.17.177", 19132))
            await asyncio.sleep(.01)
            recvData = s.recvfrom(2048)
        except BlockingIOError:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Xenon BE is either offline or unavailable at the moment. Did you type the ip correctly?"))
            return
        except socket.gaierror:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Xenon BE is either offline or unavailable at the moment. Did you type the ip correctly?"))
            return
        pong = UNCONNECTED_PONG()
        pong.buffer = recvData[0]
        pong.decode()
        sInfo = str(pong.serverName)[2:-2].split(";")
        pCount = sInfo[4]
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Xenon BE is online with "+pCount+" player(s)."))
        await ctx.trigger_typing()
        status = MinecraftServer.lookup("172.10.17.177:25565")
        try:
            status = status.status()
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Xenon JE is online with {0} player(s) and a ping of {1} ms.".format(status.players.online, status.latency)))
        except Exception:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Xenon JE is either offline or unavailable at the moment."))

def setup(bot):
    bot.add_cog(Xenon(bot))