import arrow
import discord
import uuid
from discord.ext import commands


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.db = self.bot.db  # the asyncpg pool

    async def fetch_user(self, uid):
        user = await self.db.fetchrow('SELECT * FROM users WHERE uid = $1', uid)

        if user is None:
            async with self.db.acquire() as con:
                await con.execute('INSERT INTO users VALUES ($1, $2, $3, $4, $5, $6, $7)',
                                  uid, 0, 0, 1, 20, 0, False)

            return await self.fetch_user(uid)

        return user

    async def fetch_balance(self, uid):  # fetches the amount of emeralds a user has
        # we can do this because self.fetch_user ensures user is not None
        return (await self.fetch_user(uid))['emeralds']

    async def set_balance(self, uid, emeralds):
        await self.fetch_user(uid)
        async with self.db.acquire() as con:
            await con.execute('UPDATE users SET emeralds = $1 WHERE uid = $2', emeralds, uid)

    async def balance_add(self, uid, amount):
        new_bal = await self.fetch_balance(uid) + amount
        await self.set_balance(uid, new_bal)
        return new_bal

    async def balance_sub(self, uid, amount):
        new_bal = await self.fetch_balance(uid) - amount
        await self.set_balance(uid, new_bal)
        return new_bal

    async def fetch_vault(self, uid):  # fetches a user's vault in the form (vault_amount, vault_max)
        await self.fetch_user(uid)
        return await self.db.fetchrow('SELECT vault_bal, vault_max FROM users WHERE uid = $1', uid)

    async def set_vault(self, uid, vault_bal, vault_max):
        await self.fetch_user(uid)
        async with self.db.acquire() as con:
            await con.execute('UPDATE users SET vault_bal = $1, vault_max = $2 WHERE uid = $1',
                              vault_bal, vault_max, uid)

    async def fetch_items(self, uid):
        await self.fetch_user(uid)
        return await self.db.fetch('SELECT * FROM items WHERE uid = $1', uid)

    async def fetch_item(self, uid, name):
        await self.fetch_user(uid)
        return await self.db.fetch('SELECT * FROM items WHERE uid = $1 AND item_name = $2', uid, name)

    async def add_item(self, uid, name, sell_price, amount):
        uuid_used = str(uuid.uuid4().int)
        async with self.db.acquire() as con:
            await con.execute('INSERT INTO items VALUES ($1, $2, $3, $4)',
                              uid, name, sell_price, amount)
        return uuid_used

    async def transfer_item(sender_id, recip_id, item_name, amount):
        original = await self.fetch_item(sender_id, item_name)
        recipient = await self.fetch_item(recip_id, item_name)
        async with self.db.acquire() as con:
            await con.execute('UPDATE items SET item_amount = $1 WHE',
                              recipient.get('item_amount') + amount, item_name, sender_id)

            await con.execute('UPDATE items SET item_amount = $1 WHERE uid = $2',
                              original.get('item_amount') - amount, sender_id)


def setup(bot):
    bot.add_cog(Database(bot))
