from discord.ext import commands
import discord
import asyncpg
import json
from random import choice, randint


class Database(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.db = self.bot.db

    def unload(self):
        self.db.close()

    async def clean(self, stuff):
        if isinstance(stuff, str):
            return stuff.replace("'", "\\'")
        return stuff

    async def get_db_value(self, table, uid, two, sett): # table(table in database), uid(context user id), two(second column with data, not uid), sett(default value that it is set to if other entry isn't there)
        val = await self.db.fetchrow(f"SELECT {two} FROM {table} WHERE {table}.id={uid}")
        if val is None:
            async with self.db.acquire() as con:
                await con.execute(f"INSERT INTO {table} VALUES ({uid}, '{sett}')")
            val = (sett,)
        return str(val[0])

    async def set_db_value(self, table, uid, two, sett):
        await self.get_db_value(table, uid, two, sett)
        async with self.db.acquire() as con:
            await con.execute(f"UPDATE {table} SET {two}='{sett}' WHERE id={uid}")

    async def get_db_values_3(self, table, uid, two, three, sett, settt): # table, user id, second column with data, third column with data, 2nd column default val, 3rd column default val
        values = await self.db.fetchrow(f"SELECT {two}, {three} FROM {table} WHERE {table}.id={uid}")
        if values is None:
            async with self.db.acquire() as con:
                await con.execute(f"INSERT INTO {table} VALUES ({uid}, '{sett}', '{settt}')")
            values = (sett, settt,)
        return values

    async def set_db_values_3(self, table, uid, two, three, sett, settt):
        await self.get_db_values_3(table, uid, two, three, sett, settt)
        async with self.db.acquire() as con:
            await con.execute(f"UPDATE {table} SET {two}='{sett}' WHERE id={uid}")
            await con.execute(f"UPDATE {table} SET {three}='{settt}' WHERE id={uid}")

    async def increment_vault_max(self, uid):
        vault = await self.get_vault(uid)
        if vault[1] < 2000:
            if choice([True, False, False, False, False, False, False, False, False, False, False, False, False, False, False]):
                await self.set_vault(uid, vault[0], vault[1] + 1)

    async def get_balance(self, uid): # Gets emeralds
        return int(await self.get_db_value("currency", uid, "amount", 0))

    async def set_balance(self, uid, amount): # Sets emeralds
        await self.set_db_value("currency", uid, "amount", amount)

    async def get_pickaxe(self, uid): # Gets pickaxe
        return await self.get_db_value("pickaxes", uid, "pickaxe", "wood")

    async def set_pickaxe(self, uid, pickaxe): # Sets pickaxe
        await self.set_db_value("pickaxes", uid, "pickaxe", pickaxe)

    async def get_bees(self, uid): # Sets jars of bees
        return int(await self.get_db_value("bees", uid, "bees", 0))

    async def set_bees(self, uid, amount):
        await self.set_db_value("bees", uid, "bees", amount)

    async def get_scrap(self, uid):
        return int(await self.get_db_value("netheritescrap", uid, "amount", 0))

    async def set_scrap(self, uid, amount):
        await self.set_db_value("netheritescrap", uid, "amount", amount)

    async def get_vault(self, uid):
        vault = await self.get_db_values_3("vault", uid, "amount", "max", 0, 0)
        return tuple(int(val) for val in vault)

    async def set_vault(self, uid, amount, _max):
        await self.set_db_values_3("vault", uid, "amount", "max", amount, _max)

    async def ban_from_bot(self, uid):
        entry = await self.db.fetchrow(f"SELECT id FROM bans WHERE bans.id={uid}")
        if entry is None:
            async with self.db.acquire() as con:
                await con.execute(f"INSERT INTO bans VALUES ({uid})")
            return "Successfully banned {0}."
        else:
            return "{0} was already banned."

    async def unban_from_bot(self, uid):
        entry = await self.db.fetchrow(f"SELECT id FROM bans WHERE bans.id={uid}")
        if entry is None:
            return "{0} was not banned."
        else:
            async with self.db.acquire() as con:
                await con.execute(f"DELETE FROM bans WHERE bans.id={uid}")
            return "{0} was successfully unbanned."
        
    async def list_bot_bans(self):
        return await self.db.fetch("SELECT * FROM bans")

    async def get_prefix(self, gid):
        prefix = await self.db.fetchrow(f"SELECT prefix FROM prefixes WHERE prefixes.gid={gid}")
        if prefix is None:
            async with self.db.acquire() as con:
                await con.execute(f"INSERT INTO prefixes VALUES ({gid}, '!!')")
            return "!!"
        return prefix[0]

    async def set_prefix(self, gid, prefix):
        await self.get_prefix(gid)
        async with self.db.acquire() as con:
            await con.execute(f"UPDATE prefixes SET prefix='{await self.clean(prefix)}' WHERE gid={gid}")

    async def drop_prefix(self, gid):
        async with self.db.acquire() as con:
            await con.execute(f"DELETE FROM prefixes WHERE prefixes.gid={gid}")

    async def get_do_replies(self, gid):
        do_replies = await self.db.fetchrow(f"SELECT reply FROM doreplies WHERE doreplies.gid={gid}")
        if do_replies is None:
            async with self.db.acquire() as con:
                await con.execute(f"INSERT INTO doreplies VALUES ({gid}, true)")
            return True
        return do_replies[0]

    async def set_do_replies(self, gid, doit):
        await self.get_do_replies(gid)
        async with self.db.acquire() as con:
            await con.execute(f"UPDATE doreplies SET reply={doit} WHERE gid={gid}")

    async def drop_do_replies(self, gid):
        async with self.db.acquire() as con:
            await con.execute(f"DELETE FROM doreplies WHERE doreplies.gid={gid}")

    async def get_items(self, uid):
        return await self.db.fetch(f"SELECT item, num, val FROM items WHERE items.id={uid}")

    async def get_item(self, uid, item):
        return await self.db.fetchrow(f"SELECT item, num, val FROM items WHERE items.id={uid} AND items.item='{await self.clean(item)}'")

    async def add_item(self, uid, item, num, val):
        _item = await self.get_item(uid, item)
        async with self.db.acquire() as con:
            if _item is None:
                await con.execute(f"INSERT INTO items VALUES ({uid}, '{await self.clean(item)}', {num}, {val})")
            else:
                await con.execute(f"UPDATE items SET num={int(_item[1])+int(num)} WHERE items.id={uid} AND items.item='{await self.clean(item)}'")

    async def remove_item(self, uid, item, num):
        _item = await self.get_item(uid, item)
        if _item is None:
            return
        n = _item[1]-num
        async with self.db.acquire() as con:
            if n > 0:
                await con.execute(f"UPDATE items SET num={n} WHERE items.id={uid} AND items.item='{await self.clean(item)}'")
            else:
                await con.execute(f"DELETE FROM items WHERE items.id={uid} AND items.item='{await self.clean(item)}'")

    async def add_warn(self, uid, mod, gid, reason):
        async with self.db.acquire() as con:
            await con.execute(f"INSERT INTO warns VALUES ({uid}, {mod}, {gid}, '{await self.clean(reason)}')")

    async def get_warns(self, uid, gid):
        return await self.db.fetch(f"SELECT * FROM warns WHERE warns.uid={uid} AND warns.gid={gid}")

    async def clear_warns(self, uid, gid):
        async with self.db.acquire() as con:
            await con.execute(f"DELETE FROM warns WHERE warns.uid={uid} AND warns.gid={gid}")


def setup(bot):
    bot.add_cog(Database(bot))
