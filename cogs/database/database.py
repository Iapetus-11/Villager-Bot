from discord.ext import commands
import discord
import psycopg2
import json
from random import choice

class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("data/keys.json", "r") as k:
            keys = json.load(k)
        self.db = psycopg2.connect(host="localhost",database="villagerbot", user="pi", password=keys["postgres"])
        self.whoismining = {}
        
    def unload(self):
        self.db.close()
        
    async def getdbv(self, table, uid, two, sett): #table(table in database), uid(context user id), two(second column with data, not uid), sett(default value that it is set to if other entry isn't there)
        cur = self.db.cursor()
        cur.execute("SELECT "+str(two)+" FROM "+str(table)+" WHERE "+str(table)+".id='"+str(uid)+"'")
        val = cur.fetchone()
        if val == None:
            cur.execute("INSERT INTO "+str(table)+" VALUES ('"+str(uid)+"', '"+str(sett)+"')")
            self.db.commit()
            val = (sett,)
        return str(val[0])
    
    async def setdbv(self, table, uid, two, sett):
        await self.getdbv(table, uid, two, sett)
        cur = self.db.cursor()
        cur.execute("UPDATE "+str(table)+" SET "+str(two)+"='"+str(sett)+"' WHERE id='"+str(uid)+"'")
        self.db.commit()
        
    async def getdbv3(self, table, uid, two, three, sett, settt): #table, user id, second column with data, third column with data, 2nd column default val, 3rd column default val
        cur = self.db.cursor()
        cur.execute("SELECT "+str(two)+" FROM "+str(table)+" WHERE "+str(table)+".id='"+str(uid)+"'")
        val2 = cur.fetchone()
        cur.execute("SELECT "+str(three)+" FROM "+str(table)+" WHERE "+str(table)+".id='"+str(uid)+"'")
        val3 = cur.fetchone()
        if val2 == None or val3 == None:
            cur.execute("INSERT INTO "+str(table)+" VALUES ('"+str(uid)+"', '"+str(sett)+"', '"+str(settt)+"')")
            self.db.commit()
            vals = (sett, settt,)
        else:
            vals = (val2[0], val3[0],)
        return vals
    
    async def setdbv3(self, table, uid, two, three, sett, settt):
        await self.getdbv3(table, uid, two, three, sett, settt)
        cur = self.db.cursor()
        cur.execute("UPDATE "+str(table)+" SET "+str(two)+"='"+str(sett)+"' WHERE id='"+str(uid)+"'")
        cur.execute("UPDATE "+str(table)+" SET "+str(three)+"='"+str(settt)+"' WHERE id='"+str(uid)+"'")
        self.db.commit()
        
    async def incrementMax(self, ctx):
        user = ctx.author
        vault = await self.getdbv3("vault", user.id, "amount", "max", 0, 0)
        if vault[1] < 2000:
            if choice([True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False,
                       False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False,
                       False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]):
                await self.setdbv3("vault", user.id, "amount", "max", vault[0], int(vault[1])+1)
        
    async def getBal(self, uid): #get emeralds
        return int(await self.getdbv("currency", uid, "amount", 0))

    async def setBal(self, uid, amount): #set emeralds
        await self.setdbv("currency", uid, "amount", amount)
        
    async def getPick(self, uid): #get pickaxe
        return await self.getdbv("pickaxes", uid, "pickaxe", "wood")
    
    async def setPick(self, uid, pickaxe): #set pickaxe
        await self.setdbv("pickaxes", uid, "pickaxe", pickaxe)
        
    async def getBees(self, uid): #set jars of bees
        return int(await self.getdbv("bees", uid, "bees", 0))
    
    async def setBees(self, uid, amount):
        await self.setdbv("bees", uid, "bees", amount)
        
    async def getScrap(self, uid):
        return int(await self.getdbv("netheritescrap", uid, "amount", 0))
        
    async def setScrap(self, uid, amount):
        await self.setdbv("netheritescrap", uid, "amount", amount)
        
    async def getVault(self, uid):
        vault = await self.getdbv3("vault", uid, "amount", "max", 0, 0)
        return tuple(int(val) for val in vault)
        
    async def setVault(self, uid, amount, maxx):
        await self.setdbv3("vault", uid, "amount", "max", amount, maxx)
        
    async def incrementVaultMax(self, uid):
        vault = await self.getVault(uid)
        if vault[1] < 2000:
            if choice([True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]):
                await self.setVault(uid, vault[0], vault[1]+1)
        
    async def botBan(self, uid):
        cur = self.db.cursor()
        cur.execute("SELECT id FROM bans WHERE bans.id='"+str(uid)+"'")
        entry = cur.fetchone()
        if entry == None:
            cur.execute("INSERT INTO bans VALUES ('"+str(uid)+"')")
            self.db.commit()
            return "Successfully banned {0}."
        else:
            return "{0} was already banned."
            
    async def botUnban(self, uid):
        cur = self.db.cursor()
        cur.execute("SELECT id FROM bans WHERE bans.id='"+str(uid)+"'")
        entry = cur.fetchone()
        if entry == None:
            return "{0} was not banned."
        else:
            cur.execute("DELETE FROM bans WHERE bans.id='"+str(uid)+"'")
            self.db.commit()
            return "{0} was successfully unbanned."
        
    async def getPrefix(self, gid):
        cur = self.db.cursor()
        cur.execute("SELECT prefix FROM prefixes WHERE prefixes.gid='"+str(gid)+"'")
        prefix = cur.fetchone()
        if prefix == None:
            cur.execute("INSERT INTO prefixes VALUES ('"+str(gid)+"', '!!')")
            self.db.commit()
            return "!!"
        return prefix[0]
    
    async def setPrefix(self, gid, prefix):
        await self.getPrefix(gid)
        cur = self.db.cursor()
        cur.execute("UPDATE prefixes SET prefix='{0}' WHERE gid='{1}'".format(prefix, gid))
        self.db.commit()

def setup(bot):
    bot.add_cog(Database(bot))