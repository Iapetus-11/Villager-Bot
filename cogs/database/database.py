from discord.ext import commands
import discord
import asyncpg
import json
from random import choice


class Database(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.db = self.bot.db

    def unload(self):
        self.db.close()

    async def getdbv(self, table, uid, two, sett): # table(table in database), uid(context user id), two(second column with data, not uid), sett(default value that it is set to if other entry isn't there)
        val = await self.db.fetchrow(f"SELECT {two} FROM {table} WHERE {table}.id='{uid}'")
        if val is None:
            async with self.db.acquire() as con:
                await con.execute(f"INSERT INTO {table} VALUES ('{uid}', '{sett}')")
            val = (sett,)
        return str(val[0])

    async def setdbv(self, table, uid, two, sett):
        await self.getdbv(table, uid, two, sett)
        async with self.db.acquire() as con:
            await con.execute(f"UPDATE {table} SET {two}='{sett}' WHERE id='{uid}'")

    async def getdbv3(self, table, uid, two, three, sett, settt): # table, user id, second column with data, third column with data, 2nd column default val, 3rd column default val
        vals = await self.db.fetchrow(f"SELECT {two}, {three} FROM {table} WHERE {table}.id='{uid}'")
        if vals is None:
            async with self.db.acquire() as con:
                await con.execute(f"INSERT INTO {table} VALUES ('{uid}', '{sett}', '{settt}')")
            vals = (sett, settt,)
        else:
            vals = (vals[0][0], vals[1][0],)
        return vals

    async def setdbv3(self, table, uid, two, three, sett, settt):
        await self.getdbv3(table, uid, two, three, sett, settt)
        async with self.db.acquire() as con:
            await con.execute(f"UPDATE {table} SET {two}='{sett}' WHERE id='{uid}'")
            await con.execute(f"UPDATE {table} SET {three}='{settt}' WHERE id='{uid}'")

    async def incrementVaultMax(self, uid):
        vault = await self.getVault(uid)
        if vault[1] < 2000:
            if choice([True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False,
                       False, False, False, False, False, False, False, False, False, False]):
                await self.setVault(uid, vault[0], vault[1]+1)

    async def getBal(self, uid): # Gets emeralds
        return int(await self.getdbv("currency", uid, "amount", 0))

    async def setBal(self, uid, amount): # Sets emeralds
        await self.setdbv("currency", uid, "amount", amount)

    async def getPick(self, uid): # Gets pickaxe
        return await self.getdbv("pickaxes", uid, "pickaxe", "wood")

    async def setPick(self, uid, pickaxe): # Sets pickaxe
        await self.setdbv("pickaxes", uid, "pickaxe", pickaxe)

    async def getBees(self, uid): # Sets jars of bees
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

    async def botBan(self, uid):
        entry = await self.db.fetchrow(f"SELECT id FROM bans WHERE bans.id='{uid}'")
        if entry is None:
            async with self.db.acquire() as con:
                await con.execute(f"INSERT INTO bans VALUES ('{uid}')")
            return "Successfully banned {0}."
        else:
            return "{0} was already banned."

    async def botUnban(self, uid):
        entry = await self.db.fetchrow(f"SELECT id FROM bans WHERE bans.id='{uid}'")
        if entry is None:
            return "{0} was not banned."
        else:
            async with self.db.acquire() as con:
                await con.execute(f"DELETE FROM bans WHERE bans.id='{uid}'")
            return "{0} was successfully unbanned."
        
    async def listBotBans(self):
        return await self.db.fetch("SELECT * FROM bans")

    async def getPrefix(self, ctx):
        if ctx.guild is None:
            return "!!"
        gid = ctx.guild.id
        prefix = await self.db.fetchrow(f"SELECT prefix FROM prefixes WHERE prefixes.gid='{gid}'")
        if prefix is None:
            async with self.db.acquire() as con:
                await con.execute(f"INSERT INTO prefixes VALUES ('{gid}', '!!')")
            return "!!"
        return prefix[0]

    async def setPrefix(self, gid, prefix):
        await self.getPrefix(gid)
        async with self.db.acquire() as con:
            await con.execute(f"UPDATE prefixes SET prefix='{prefix}' WHERE gid='{gid}'")

    async def getDoReplies(self, gid):
        dothatshit = await self.db.fetchrow(f"SELECT reply FROM doreplies WHERE doreplies.gid='{gid}'")
        if dothatshit is None:
            async with self.db.acquire() as con:
                await con.execute(f"INSERT INTO doreplies VALUES ('{gid}', true)")
            return True
        return dothatshit[0]

    async def setDoReplies(self, gid, doit):
        await self.getDoReplies(gid)
        async with self.db.acquire() as con:
            await con.execute(f"UPDATE doreplies SET reply={doit} WHERE gid='{gid}'")

    async def dropDoReplies(self, gid):
        async with self.db.acquire() as con:
            await con.execute(f"DELETE FROM doreplies WHERE doreplies.gid='{gid}'")

    async def getItems(self, uid):
        return await self.db.fetch(f"SELECT item, num, val FROM items WHERE items.id='{uid}'")

    async def getItem(self, uid, item):
        return await self.db.fetchrow(f"SELECT item, num, val FROM items WHERE items.id='{uid}' AND items.item='{item}'")

    async def addItem(self, uid, item, num, val):
        itemm = await self.getItem(uid, item)
        async with self.db.acquire() as con:
            if itemm is None:
                await con.execute(f"INSERT INTO items VALUES ('{uid}', '{item}', {num}, {val})")
            else:
                await con.execute(f"UPDATE items SET num={int(itemm[1])+int(num)} WHERE items.id='{uid}' AND items.item='{item}'")

    async def removeItem(self, uid, item, num):
        itemm = await self.getItem(uid, item)
        if itemm is None:
            return
        n = itemm[1]-num
        async with self.db.acquire() as con:
            if n > 0:
                await con.execute(f"UPDATE items SET num={n} WHERE items.id='{uid}' AND items.item='{item}'")
            else:
                await con.execute(f"DELETE FROM items WHERE items.id='{uid}' AND items.item='{item}'")


def setup(bot):
    bot.add_cog(Database(bot))
