from discord.ext import commands
import discord
import asyncpg
import json
from random import choice


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open("data/keys.json", "r") as k:
            keys = json.load(k)

        self.bot.loop.create_task(self.dbHandler(True))

    def unload(self):
        self.bot.loop.create_task(self.dbHandler(False))

    async def dbHandler(self, do_connect):
        if do_connect:
            self.db = await asyncpg.connect(host="localhost", database="villagerbot", user="pi", password=keys["postgres"])
        else:
            await self.db.close()

    async def getdbv(self, table, uid, two, sett): # table(table in database), uid(context user id), two(second column with data, not uid), sett(default value that it is set to if other entry isn't there)
        val = await self.db.fetchrow(f"SELECT {two} FROM {table} WHERE {table}.id='{uid}'")
        if val is None:
            await self.db.execute(f"INSERT INTO {table} VALUES ('{uid}', '{sett}')")
            await self.db.commit()
            val = (sett,)
        return str(val[0])

    async def setdbv(self, table, uid, two, sett):
        await self.getdbv(table, uid, two, sett)
        await self.db.execute(f"UPDATE {table} SET {two}='{sett}' WHERE id='{uid}'")
        await self.db.commit()

    async def getdbv3(self, table, uid, two, three, sett, settt): # table, user id, second column with data, third column with data, 2nd column default val, 3rd column default val
        vals = await self.db.fetchrow(f"SELECT {two}, {three} FROM {table} WHERE {table}.id='{uid}'")
        val2 = vals[0]
        val3 = vals[1]
        if val2 is None or val3 is None:
            await self.db.execute(f"INSERT INTO {table} VALUES ('{uid}', '{sett}', '{settt}')")
            await self.db.commit()
            vals = (sett, settt,)
        else:
            vals = (val2[0], val3[0],)
        return vals

    async def setdbv3(self, table, uid, two, three, sett, settt):
        await self.getdbv3(table, uid, two, three, sett, settt)
        await self.db.execute(f"UPDATE {table} SET {two}='{sett}' WHERE id='{uid}'")
        await self.db.execute(f"UPDATE {table} SET {three}='{settt}' WHERE id='{uid}'")
        await self.db.commit()

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
            await self.db.execute(f"INSERT INTO bans VALUES ('{uid}')")
            await self.db.commit()
            return "Successfully banned {0}."
        else:
            return "{0} was already banned."

    async def botUnban(self, uid):
        entry = await self.db.fetchrow(f"SELECT id FROM bans WHERE bans.id='{uid}'")
        if entry is None:
            return "{0} was not banned."
        else:
            await self.db.execute(f"DELETE FROM bans WHERE bans.id='{uid}'")
            await self.db.commit()
            return "{0} was successfully unbanned."

    async def listBotBans(self):
        bans = await self.db.fetch("SELECT * FROM bans")
        return bans

    async def getPrefix(self, gid):
        prefix = await self.db.fetchrow(f"SELECT prefix FROM prefixes WHERE prefixes.gid='{gid}'")
        if prefix is None:
            await self.db.execute(f"INSERT INTO prefixes VALUES ('{gid}', '!!')")
            await self.db.commit()
            return "!!"
        return prefix[0]

    async def setPrefix(self, gid, prefix):
        await self.getPrefix(gid)
        await self.db.execute(f"UPDATE prefixes SET prefix='{prefix}' WHERE gid='{gid}'")
        await self.db.commit()

    async def getDoReplies(self, gid):
        await self.db.fetchrow(f"SELECT reply FROM doreplies WHERE doreplies.gid='{gid}'")
        if dothatshit is None:
            await self.db.execute(f"INSERT INTO doreplies VALUES ('{gid}', true)")
            await self.db.commit()
            return True
        return dothatshit[0]

    async def setDoReplies(self, gid, doit):
        await self.getDoReplies(gid)
        await self.db.execute(f"UPDATE doreplies SET reply={doit} WHERE gid='{gid}'")
        await self.db.commit()

    async def dropDoReplies(self, gid):
        await self.db.execute(f"DELETE FROM doreplies WHERE doreplies.gid='{gid}'")
        await self.db.commit()

    async def getItems(self, uid):
        return await self.db.fetch(f"SELECT item, num, val FROM items WHERE items.id='{uid}'")

    async def getItem(self, uid, item):
        return await self.db.fetchrow(f"SELECT item, num, val FROM items WHERE items.id='{uid}' AND items.item='{item}'")

    async def addItem(self, uid, item, num, val):
        itemm = await self.getItem(uid, item)
        if itemm is None:
            await self.db.execute(f"INSERT INTO items VALUES ('{uid}', '{item}', {num}, {val})")
        else:
            await self.db.execute(f"UPDATE items SET num={int(itemm[1])+int(num)} WHERE items.id='{uid}' AND items.item='{item}'")
        await self.db.commit()

    async def removeItem(self, uid, item, num):
        itemm = await self.getItem(uid, item)
        if itemm is None:
            return
        n = itemm[1]-num
        if n > 0:
            await self.db.execute(f"UPDATE items SET num={n} WHERE items.id='{uid}' AND items.item='{item}'")
        else:
            await self.db.execute(f"DELETE FROM items WHERE items.id='{uid}' AND items.item='{item}'")
        await self.db.commit()


def setup(bot):
    bot.add_cog(Database(bot))
