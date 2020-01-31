from discord.ext import commands
import discord
import socket
from pyraklib.protocol.EncapsulatedPacket import EncapsulatedPacket
from pyraklib.protocol.UNCONNECTED_PING import UNCONNECTED_PING
from pyraklib.protocol.UNCONNECTED_PONG import UNCONNECTED_PONG
from mcstatus import MinecraftServer
import asyncio
from yandex.Translater import Translater
import json

class Xenon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("keys.json", "r") as k:
            keys = json.load(k)
        self.yTrKey = keys["ytr"]
        self.tr = Translater()
        self.tr.set_key(self.yTrKey)
        
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild == None:
            return
        if "discord.gg" in message.content:
            if message.guild.id in [593954944059572235, 641117791272960031]:
                if message.channel.id not in [659137844257882112, 594017826033893377, 645827431634042882]:
                    try:
                        await message.delete()
                        await message.channel.send(embed=discord.Embed(color=discord.Color.green(), description=message.author.mention+", Discord server links aren't allowed here!"))
                    except Exception:
                        pass
                    
        if message.author.id == 639492331757895702 and message.guild.id == 641117791272960031:
            if message.clean_content == "" or message.clean_content == None:
                return
            self.tr.set_from_lang("ru")
            self.tr.set_to_lang("en")
            self.tr.set_text(message.clean_content)
            await message.channel.send(self.tr.translate())
            
        if message.guild.id == 641117791272960031:
            if message.clean_content is not "":
                if message.author.id not in [639492331757895702, 639498607632056321]:
                    self.tr.set_from_lang("en")
                    self.tr.set_to_lang("ru")
                    self.tr.set_text(message.clean_content)
                    await self.bot.get_channel(672318808664309760).send("**"+message.author.display_name+"**: "+self.tr.translate())
            
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id == 593954944059572235:
            await self.bot.get_channel(593988932564418590).send("Hey "+member.mention+", welcome to **Xenon**! Please read through the "+self.bot.get_channel(593997092234461194).mention+".")
        if member.guild.id == 641117791272960031:
            await self.bot.get_channel(643269881919438860).send("Welcome to the Villager Bot support server, "+member.mention+"!")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id == 593954944059572235:
            await self.bot.get_channel(593988932564418590).send("Goodbye, "+member.mention)
        if member.guild.id == 641117791272960031:
            await self.bot.get_channel(643269881919438860).send("Goodbye, "+member.mention)
    
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