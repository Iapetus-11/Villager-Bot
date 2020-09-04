import discord
from discord.ext import commands


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.db = self.bot.db  # the asyncpg pool

    async def fetch_user(self, uid):
        user = await self.db.fetchrow('SELECT * FROM users WHERE uid = $1', uid)

        if user is None:
            async with self.db.acquire() as con:
                await con.execute(
                    'INSERT INTO users VALUES ($1, $2, $3, $4, $5, $6, $7)',
                    uid, 0, 0, 1, 20, 0, False
                )

                await self.add_item(uid, 'Wood Pickaxe', 0, 1)
                await self.add_item(uid, 'Wood Sword', 0, 1)

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
            await con.execute('UPDATE users SET vault_bal = $1, vault_max = $2 WHERE uid = $3',
                              vault_bal, vault_max, uid)

    async def fetch_items(self, uid):
        await self.fetch_user(uid)
        return await self.db.fetch('SELECT * FROM items WHERE uid = $1', uid)

    async def fetch_item(self, uid, name):
        await self.fetch_user(uid)
        return await self.db.fetchrow('SELECT * FROM items WHERE uid = $1 AND LOWER(name) = LOWER($2)', uid, name)

    async def add_item(self, uid, name, sell_price, amount):
        prev = await self.fetch_item(uid, name)

        async with self.db.acquire() as con:
            if prev is None:
                await con.execute('INSERT INTO items VALUES ($1, $2, $3, $4)',
                                  uid, name, sell_price, amount)
            else:
                await con.execute('UPDATE items SET amount = $1 WHERE uid = $2 AND LOWER(name) = LOWER($3)',
                                  amount + prev['amount'], uid, name)

    async def remove_item(self, uid, name, amount):
        prev = await self.fetch_item(uid, name)

        async with self.db.acquire() as con:
            if prev['amount'] - amount < 1:
                await con.execute('DELETE FROM items WHERE uid = $1 AND name = $2', uid, name)
            else:
                await con.execute('UPDATE items SET amount = $1 WHERE uid = $2 AND LOWER(name) = LOWER($3)',
                                  prev['amount'] - amount, uid, name)

    async def fetch_pickaxe(self, uid):
        items_names = [item['name'] for item in await self.fetch_items(uid)]

        for pickaxe in self.bot.d.mining.pickaxes:
            if pickaxe in items_names:
                return pickaxe

        await self.add_item(uid, 'Wood Pickaxe', 0, 1)
        return self.bot.d.mining.pickaxes[-1]

    async def fetch_sword(self, uid):
        pass

    async def rich_trophy_wipe(self, uid):
        await self.set_balance(uid, 0)
        await self.set_vault(uid, 0, 0)

        async with self.db.acquire() as con:
            await con.execute('DELETE FROM items WHERE uid = $1 AND name != $2 AND name != $3',
                              uid, 'Rich Person Trophy', 'Bane Of Pillagers Amulet')

    async def fetch_user_lb(self, uid):
        lbs = await self.db.fetchrow('SELECT * FROM leaderboards WHERE uid = $1', uid)

        if lbs is None:
            async with self.db.acquire() as con:
                await con.execute(
                    'INSERT INTO leaderboards VALUES ($1, $2, $3, $4, $5, $6)',
                    uid, 0, 0, 0, 0, 0
                )

    async def update_lb(self, uid, lb, value, mode='add'):
        prev = await self.fetch_user_lb(uid)
        prev_lb_val = 0 if prev is None else prev[lb]

        if mode == 'add':
            async with self.db.acquire() as con:
                await con.execute(f'UPDATE leaderboards SET {lb} = $1 WHERE uid = $2', prev_lb_val + value, uid)
        elif mode == 'sub':
            async with self.db.acquire() as con:
                await con.execute(f'UPDATE leaderboards SET {lb} = $1 WHERE uid = $2', prev_lb_val - value, uid)
        elif mode == 'set':
            async with self.db.acquire() as con:
                await con.execute(f'UPDATE leaderboards SET {lb} = $1 WHERE uid = $2', value, uid)

    async def fetch_random_server(self):
        return await self.db.fetchrow('SELECT * FROM mc_servers ORDER BY RANDOM() LIMIT 1')

    async def add_server(self, owner_id, address, port, version, note=None):
        async with self.db.acquire() as con:
            await con.execute(
                'INSERT INTO mc_servers VALUES ($1, $2, $3, $4, $5)',
                owner_id, address, port, version, note
            )

def setup(bot):
    bot.add_cog(Database(bot))
