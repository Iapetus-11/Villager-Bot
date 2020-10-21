from discord.ext import commands, tasks
import discord


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.d = self.bot.d

        self.db = self.bot.db  # the asyncpg pool

        self.update_user_health.start()

    def cog_unload(self):
        self.update_user_health.cancel()

    @tasks.loop(seconds=10)
    async def update_user_health(self):
        async with self.db.acquire() as con:
            await con.execute('UPDATE users SET health = health + 2 WHERE health < 20')

    @update_user_health.before_loop
    async def before_update_user_health(self):
        await self.bot.wait_until_ready()

    async def fetch_all_botbans(self):
        botban_records = await self.db.fetch('SELECT uid FROM users WHERE bot_banned = true')  # returns [Record<uid=>, Record<uid=>,..]
        return [r[0] for r in botban_records]

    async def fetch_all_guild_langs(self):
        lang_records = await self.db.fetch('SELECT gid, lang FROM guilds')
        return dict((r[0], r[1],) for r in lang_records if (r[1] != 'en_us' and r[1] != None))  # needs to be a dict

    async def fetch_all_guild_prefixes(self):
        prefix_records = await self.db.fetch('SELECT gid, prefix FROM guilds')
        return dict((r[0], r[1],) for r in prefix_records if (r[1] != self.d.default_prefix and r[1] != None))  # needs to be a dict

    async def fetch_guild(self, gid):
        g = await self.db.fetchrow('SELECT * FROM guilds WHERE gid = $1', gid)

        if g is None:
            async with self.db.acquire() as con:
                await con.execute(
                    'INSERT INTO guilds VALUES ($1, $2, $3, $4, $5, $6)',
                    gid, '/', True, 'easy', 'en_us', None
                )

            return await self.fetch_guild(gid)

        return g

    async def set_guild_attr(self, gid, attr, value):
        await self.fetch_guild(gid)  # ensure it exists in db
        async with self.db.acquire() as con:
            await con.execute(f'UPDATE guilds SET {attr} = $1 WHERE gid = $2', value, gid)

    async def drop_guild(self, gid):
        async with self.db.acquire() as con:
            await con.execute('DELETE FROM guilds WHERE gid = $1', gid)

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

    async def update_user(self, uid, key, value):
        await self.fetch_user(uid)

        async with self.db.acquire() as con:
            await con.execute(f'UPDATE users SET {key} = $1 WHERE uid = $2', value, uid)

    async def fetch_balance(self, uid):  # fetches the amount of emeralds a user has
        # we can do this because self.fetch_user ensures user is not None
        return (await self.fetch_user(uid))['emeralds']

    async def mass_fetch_balances(self):
        return await self.db.fetch('SELECT uid, emeralds FROM users')

    async def set_balance(self, uid, emeralds):
        await self.fetch_user(uid)
        async with self.db.acquire() as con:
            await con.execute('UPDATE users SET emeralds = $1 WHERE uid = $2', emeralds, uid)

    async def balance_add(self, uid, amount):
        new_bal = await self.fetch_balance(uid) + amount
        await self.set_balance(uid, new_bal)
        return new_bal

    async def balance_sub(self, uid, taken):
        bal = await self.fetch_balance(uid)
        taken = 0 if bal - taken <= 0 else taken
        await self.set_balance(uid, bal - taken)
        return taken

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

    async def mass_fetch_item(self, name):
        return await self.db.fetch('SELECT * FROM items WHERE LOWER(name) = LOWER($1)', name)

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
                await con.execute('DELETE FROM items WHERE uid = $1 AND LOWER(name) = LOWER($2)', uid, name)
            else:
                await con.execute('UPDATE items SET amount = $1 WHERE uid = $2 AND LOWER(name) = LOWER($3)',
                                  prev['amount'] - amount, uid, name)

    async def fetch_pickaxe(self, uid):
        items_names = [item['name'] for item in await self.fetch_items(uid)]

        for pickaxe in self.d.mining.pickaxes:
            if pickaxe in items_names:
                return pickaxe

        await self.add_item(uid, 'Wood Pickaxe', 0, 1)
        return 'Wood Pickaxe'

    async def fetch_sword(self, uid):
        items_names = [item['name'] for item in await self.fetch_items(uid)]

        for sword in ('Netherite Sword', 'Diamond Sword', 'Gold Sword', 'Iron Sword', 'Stone Sword', 'Wood Sword'):
            if sword in items_names:
                return sword

        await self.add_item(uid, 'Wood Sword', 0, 1)
        return 'Wood Sword'

    async def rich_trophy_wipe(self, uid):
        await self.set_balance(uid, 0)
        await self.set_vault(uid, 0, 1)

        async with self.db.acquire() as con:
            await con.execute('DELETE FROM items WHERE uid = $1 AND name != $2 AND name != $3',
                              uid, 'Rich Person Trophy', 'Bane Of Pillagers Amulet')

    async def fetch_user_lb(self, uid):
        lbs = await self.db.fetchrow('SELECT * FROM leaderboards WHERE uid = $1', uid)

        if lbs is None:
            async with self.db.acquire() as con:
                await con.execute('INSERT INTO leaderboards VALUES ($1, $2, $3)', uid, 0, 0)

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

    async def mass_fetch_leaderboard(self, lb):
        return await self.db.fetch(f'SELECT uid, {lb} FROM leaderboards')

    async def set_botbanned(self, uid, botbanned):
        await self.fetch_user(uid)

        if botbanned:
            self.d.ban_cache.append(uid)
        else:
            try:
                self.d.ban_cache.pop(self.d.ban_cache.index(uid))
            except KeyError:
                pass

        async with self.db.acquire() as con:
            await con.execute('UPDATE users SET bot_banned = $1 WHERE uid = $2', botbanned, uid)

    async def add_warn(self, uid, gid, mod_id, reason):
        async with self.db.acquire() as con:
            await con.execute(
                'INSERT INTO warnings VALUES ($1, $2, $3, $4)',
                uid, gid, mod_id, reason
            )

    async def fetch_warns(self, uid, gid):
        return await self.db.fetch('SELECT * FROM warnings WHERE uid = $1 AND gid = $2', uid, gid)

    async def clear_warns(self, uid, gid):
        async with self.db.acquire() as con:
            await con.execute('DELETE FROM warnings WHERE uid = $1 AND gid = $2', uid, gid)


def setup(bot):
    bot.add_cog(Database(bot))
