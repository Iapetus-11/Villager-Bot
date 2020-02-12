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
import psycopg2

class Xenon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("keys.json", "r") as k:
            keys = json.load(k)
        self.db = psycopg2.connect(host="localhost",database="villagerbot", user="pi", password=keys["postgres"])
        self.yTrKey = keys["ytr"]
        self.tr = Translater()
        self.tr.set_key(self.yTrKey)
        self.admin_roles= [594000312776261632, 594000647360217115, 593960578045706246]
        
    def cog_unload(self):
        self.db.close()
        
    def xenon_only(ctx): #only in Xenon and le Support Server
        if ctx.guild == None or ctx.guild is None:
            return False
        if ctx.guild.id == 593954944059572235 or ctx.guild.id == 641117791272960031:
            return True
        return False
        
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild == None or message.guild is None:
            return False
        if message.guild.id != 593954944059572235 and message.guild.id != 641117791272960031:
            return False
        if "discord.gg" in message.content: #anti-advert
            if message.channel.id not in [659137844257882112, 594017826033893377, 645827431634042882, 643648150778675202, 648037815791255586]:
                try:
                    await message.delete()
                    await message.channel.send(embed=discord.Embed(color=discord.Color.green(), description=message.author.mention+", Discord server links aren't allowed here!"))
                except Exception:
                    pass
                    
        if message.author.id == 639492331757895702 and message.guild.id == 641117791272960031: #Villager Bot support server russian to english
            if message.clean_content == "" or message.clean_content == None:
                return
            self.tr.set_from_lang("ru")
            self.tr.set_to_lang("en")
            self.tr.set_text(message.clean_content)
            await message.channel.send(self.tr.translate())
            
        if message.guild.id == 641117791272960031: #Villager Bot support server english to russian channel
            if message.clean_content is not "":
                if message.author.id not in [639492331757895702, 639498607632056321]:
                    self.tr.set_from_lang("en")
                    self.tr.set_to_lang("ru")
                    self.tr.set_text(message.clean_content)
                    await self.bot.get_channel(672318808664309760).send("**"+message.author.display_name+"**: "+self.tr.translate())
            
    @commands.Cog.listener()
    @commands.check(xenon_only)
    async def on_member_join(self, member):
        if member.guild.id == 593954944059572235:
            await self.bot.get_channel(593988932564418590).send("Hey "+member.mention+", welcome to **Xenon**! Please read through the "+self.bot.get_channel(593997092234461194).mention+".")
        if member.guild.id == 641117791272960031:
            await self.bot.get_channel(643269881919438860).send("Welcome to the Villager Bot support server, "+member.mention+"!")
    
    @commands.Cog.listener()
    @commands.check(xenon_only)
    async def on_member_remove(self, member):
        if member.guild.id == 593954944059572235:
            await self.bot.get_channel(593988932564418590).send("Goodbye, "+member.mention+" ("+member.display_name+")")
        if member.guild.id == 641117791272960031:
            await self.bot.get_channel(643269881919438860).send("Goodbye, "+member.mention+" ("+member.display_name+")")
            
    async def statusBE(self, ctx):
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
        
    async def statusJE(self, ctx):
        await ctx.trigger_typing()
        status = MinecraftServer.lookup("172.10.17.177:25565")
        try:
            status = status.status()
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Xenon JE is online with {0} player(s) and a ping of {1} ms.".format(status.players.online, status.latency)))
        except Exception:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Xenon JE is either offline or unavailable at the moment."))
    
    @commands.command(name="mcstatus")
    @commands.check(xenon_only)
    async def mcstatus(self, ctx):
        await self.statusBE(ctx)
        await self.statusJE(ctx)

    @commands.command(name="warn")
    async def warn(self, ctx, user: discord.User, *, reason: str):
        if not ctx.guild.id == 593954944059572235:
            return
        if ctx.author.top_role.id not in self.admin_roles:
            return
        if ctx.author.id == user.id:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You cannot warn yourself."))
            return
        cur = self.db.cursor()
        cur.execute("INSERT INTO warnings VALUES ('"+str(user.id)+"', '"+reason+"')")
        self.db.commit()
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Warned "+user.mention+". Reason: *"+reason+"*"))
        cur.execute("SELECT * FROM warnings WHERE warnings.id='"+str(user.id)+"'")
        warnings = cur.fetchall()
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=user.mention+" now has "+len(warnings)+" warnings."))
        
    @commands.command(name="warns", aliases=["warnings"])
    async def warns(self, ctx, user: discord.User):
        if not ctx.guild.id == 593954944059572235:
            return
        if ctx.author.top_role.id not in self.admin_roles:
            return
        cur = self.db.cursor()
        cur.execute("SELECT * FROM warnings WHERE warnings.id='"+str(user.id)+"'")
        warnings = cur.fetchall()
        if len(warnings) == 0:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="No warnings found for user "+str(user)+"."))
            return
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Warnings for user "+str(user)+":"))
        rows = 10
        i = 0
        warningg = ""
        for warning in warnings:
            i += 1
            warningg += "\n"+str(i)+". "+str(warning[1])
            if i%rows == 0:
                await ctx.send(warningg)
                warningg = ""
        if warningg is not "":
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=warningg))
            
    @commands.command(name="clearwarns", aliases=["clearwarnings", "warnsclear", "warningsclear"])
    async def clearwarns(self, ctx, user: discord.User):
        if not ctx.guild.id == 593954944059572235:
            return
        if ctx.author.top_role.id not in self.admin_roles:
            return
        if ctx.author.id == user.id and not ctx.author.id == 536986067140608041:
            await ctx.send("You cannot clear your own warnings.")
            return
        cur = self.db.cursor()
        cur.execute("DELETE FROM warnings WHERE warnings.id='"+str(user.id)+"'")
        self.db.commit()
        await ctx.send("Cleared all of "+str(user)+"'s warnings.")

def setup(bot):
    bot.add_cog(Xenon(bot))