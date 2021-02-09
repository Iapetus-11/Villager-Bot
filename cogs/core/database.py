from discord.ext import commands, tasks
import discord


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = bot.d

        self.db = bot.db  # the asyncpg pool

        self.update_user_health.start()
        self.update_support_server_member_roles.start()

        self._user_cache = {}  # {uid: record}

    def cog_unload(self):
        self.update_user_health.cancel()
        self.update_support_server_member_roles.cancel()

    async def populate_caches(self):
        self.d.ban_cache = await self.fetch_all_botbans()
        self.d.lang_cache = await self.fetch_all_guild_langs()
        self.d.prefix_cache = await self.fetch_all_guild_prefixes()
        self.d.additional_mcservers = await self.fetch_all_mcservers()
        self.d.disabled_cmds = await self.fetch_all_disabled_commands()

    def cache_user(self, uid, user):
        self._user_cache[uid] = user
        return user

    def uncache_user(self, uid):
        try:
            del self._user_cache[uid]
        except KeyError:
            pass

    @tasks.loop(seconds=16)
    async def update_user_health(self):
        async with self.db.acquire() as con:
            await con.execute('UPDATE users SET health = health + 1 WHERE health < 20')

    @tasks.loop(minutes=10)
    async def update_support_server_member_roles(self):
        await self.bot.wait_until_ready()

        support_guild = self.bot.get_guild(self.d.support_server_id)
        role_map_values = list(self.d.role_mappings.values())

        for member in support_guild.members:
            roles = []

            if support_guild.get_member(member.id) is None:
                continue

            for role in member.roles:
                if role.id not in role_map_values and role.id != self.d.support_server_id:
                    roles.append(role)

            pickaxe_role = self.d.role_mappings.get(await self.fetch_pickaxe(member.id))
            if pickaxe_role is not None:
                roles.append(support_guild.get_role(pickaxe_role))

            if await self.fetch_item(member.id, 'Bane Of Pillagers Amulet') is not None:
                roles.append(support_guild.get_role(self.d.role_mappings.get('BOP')))

            if roles != member.roles:
                try:
                    await member.edit(roles=roles)
                except Exception:
                    pass

    async def fetch_all_botbans(self):
        async with self.db.acquire() as con:
            botban_records = await con.fetch('SELECT uid FROM users WHERE bot_banned = true')  # returns [Record<uid=>, Record<uid=>,..]

        return [r[0] for r in botban_records]

    async def fetch_all_guild_langs(self):
        async with self.db.acquire() as con:
            lang_records = await con.fetch('SELECT gid, lang FROM guilds')

        return dict((r[0], r[1],) for r in lang_records if (r[1] != 'en' and r[1] != None and r[1] != 'en_us'))  # needs to be a dict

    async def fetch_all_guild_prefixes(self):
        async with self.db.acquire() as con:
            prefix_records = await con.fetch('SELECT gid, prefix FROM guilds')

        return dict((r[0], r[1],) for r in prefix_records if (r[1] != self.d.default_prefix and r[1] != None))  # needs to be a dict

    async def fetch_all_mcservers(self):
        async with self.db.acquire() as con:
            servers = await con.fetch('SELECT host, link FROM mcservers')

        return [(s['host'], s['link'],) for s in servers]

    async def fetch_all_disabled_commands(self):
        async with self.db.acquire() as con:
            disabled = await con.fetch('SELECT * FROM disabled')

        disabled_nice = {}

        for entry in disabled:
            disabled_nice[entry['gid']] = disabled_nice.get(entry['gid'], []) + [entry[1]]

        return disabled_nice

    async def fetch_guild(self, gid, con=None):
        made_con = False
        if con is None:
            con = await self.db.acquire()
            made_con = True

        try:
            g = await con.fetchrow('SELECT * FROM guilds WHERE gid = $1', gid)

            if g is None:
                await con.execute(
                    'INSERT INTO guilds VALUES ($1, $2, $3, $4, $5, $6, $7)',
                    gid, '/', True, 'easy', 'en', None, False
                )

                return await self.fetch_guild(gid, con)

            return g
        finally:
            if made_con:
                await self.db.release(con)

    async def set_guild_attr(self, gid, attr, value):
        async with self.db.acquire() as con:
            await self.fetch_guild(gid, con)  # ensure it exists in db
            await con.execute(f'UPDATE guilds SET {attr} = $1 WHERE gid = $2', value, gid)

    async def drop_guild(self, gid):
        async with self.db.acquire() as con:
            await con.execute('DELETE FROM guilds WHERE gid = $1', gid)

    async def fetch_guild_premium(self, gid):
        async with self.db.acquire() as con:
            return bool(await con.fetchval('SELECT premium FROM guilds WHERE gid = $1', gid))

    async def set_cmd_usable(self, gid, cmd, usable):
        async with self.db.acquire() as con:
            if usable:
                await con.execute('DELETE FROM disabled WHERE gid = $1 AND cmd = $2', gid, cmd)
            else:
                await con.execute('INSERT INTO disabled VALUES ($1, $2)', gid, cmd)

    async def fetch_user(self, uid, con=None):
        try:
            return self._user_cache[uid]
        except KeyError:
            self.uncache_user(uid)

        made_con = False
        if con is None:
            con = await self.db.acquire()
            made_con = True

        try:
            user = await con.fetchrow('SELECT * FROM users WHERE uid = $1', uid)

            if user is None:
                await con.execute(
                    'INSERT INTO users VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)',
                    uid, 0, 0, 1, 20, False, 0, 0, False
                )

                await self.add_item(uid, 'Wood Pickaxe', 0, 1, True)
                await self.add_item(uid, 'Wood Sword', 0, 1, True)

                return await self.fetch_user(uid, con)

            return self.cache_user(uid, user)
        finally:
            if made_con:
                await self.db.release(con)

    async def update_user(self, uid, key, value):
        async with self.db.acquire() as con:
            await self.fetch_user(uid, con)
            await con.execute(f'UPDATE users SET {key} = $1 WHERE uid = $2', value, uid)

        self.uncache_user(uid)

    async def fetch_balance(self, uid):  # fetches the amount of emeralds a user has
        # we can do this because self.fetch_user ensures user is not None
        return (await self.fetch_user(uid))['emeralds']

    async def mass_fetch_balances(self):
        async with self.db.acquire() as con:
            return await con.fetch('SELECT uid, emeralds FROM users WHERE emeralds > 0 AND bot_banned = false')

    async def mass_fetch_votestreaks(self):
        async with self.db.acquire() as con:
            return await con.fetch('SELECT uid, vote_streak FROM users WHERE vote_streak > 0 AND bot_banned = false')

    async def set_balance(self, uid, emeralds):
        async with self.db.acquire() as con:
            await self.fetch_user(uid, con)
            await con.execute('UPDATE users SET emeralds = $1 WHERE uid = $2', emeralds, uid)

        self.uncache_user(uid)

    async def balance_add(self, uid, amount):
        new_bal = await self.fetch_balance(uid) + amount
        await self.set_balance(uid, new_bal)
        self.uncache_user(uid)
        return new_bal

    async def balance_sub(self, uid, amount):
        bal = await self.fetch_balance(uid)
        new = bal - amount

        if new < 0:
            amount = bal
            new = 0

        await self.set_balance(uid, new)
        self.uncache_user(uid)
        return amount

    async def fetch_vault(self, uid):  # fetches a user's vault in the form (vault_amount, vault_max)
        async with self.db.acquire() as con:
            await self.fetch_user(uid, con)
            return await con.fetchrow('SELECT vault_bal, vault_max FROM users WHERE uid = $1', uid)

    async def set_vault(self, uid, vault_bal, vault_max):
        async with self.db.acquire() as con:
            await self.fetch_user(uid, con)
            await con.execute(
                'UPDATE users SET vault_bal = $1, vault_max = $2 WHERE uid = $3',
                vault_bal, vault_max, uid
            )

        self.uncache_user(uid)

    async def fetch_items(self, uid):
        async with self.db.acquire() as con:
            await self.fetch_user(uid, con)
            return await con.fetch('SELECT * FROM items WHERE uid = $1', uid)

    async def fetch_item(self, uid, name):
        async with self.db.acquire() as con:
            await self.fetch_user(uid, con)
            return await con.fetchrow('SELECT * FROM items WHERE uid = $1 AND LOWER(name) = LOWER($2)', uid, name)

    async def mass_fetch_item(self, name):
        async with self.db.acquire() as con:
            return await con.fetch('SELECT * FROM items WHERE LOWER(name) = LOWER($1)', name)

    async def add_item(self, uid, name, sell_price, amount, sticky=False):
        prev = await self.fetch_item(uid, name)

        async with self.db.acquire() as con:
            if prev is None:
                await con.execute(
                    'INSERT INTO items VALUES ($1, $2, $3, $4, $5)',
                    uid, name, sell_price, amount, sticky
                )
            else:
                await con.execute(
                    'UPDATE items SET amount = $1 WHERE uid = $2 AND LOWER(name) = LOWER($3)',
                    amount + prev['amount'], uid, name
                )

    async def remove_item(self, uid, name, amount):
        prev = await self.fetch_item(uid, name)

        async with self.db.acquire() as con:
            if prev['amount'] - amount < 1:
                await con.execute('DELETE FROM items WHERE uid = $1 AND LOWER(name) = LOWER($2)', uid, name)
            else:
                await con.execute(
                    'UPDATE items SET amount = $1 WHERE uid = $2 AND LOWER(name) = LOWER($3)',
                    prev['amount'] - amount, uid, name
                )

    async def log_transaction(self, item, amount, timestamp, giver, receiver):
        async with self.db.acquire() as con:
            await con.execute('INSERT INTO give_logs VALUES ($1, $2, $3, $4, $5)', item, amount, timestamp, giver, receiver)

    async def fetch_transactions_by_sender(self, uid, limit):
        async with self.db.acquire() as con:
            return await con.fetch(
                'SELECT * FROM give_logs WHERE giver_uid = $1 ORDER BY ts DESC LIMIT $2',
                uid, limit
            )

    async def fetch_pickaxe(self, uid):
        items_names = [item['name'] for item in await self.fetch_items(uid)]

        for pickaxe in self.d.mining.pickaxes:
            if pickaxe in items_names:
                return pickaxe

        await self.add_item(uid, 'Wood Pickaxe', 0, 1, True)
        return 'Wood Pickaxe'

    async def fetch_sword(self, uid):
        items_names = [item['name'] for item in await self.fetch_items(uid)]

        for sword in ('Netherite Sword', 'Diamond Sword', 'Gold Sword', 'Iron Sword', 'Stone Sword', 'Wood Sword'):
            if sword in items_names:
                return sword

        await self.add_item(uid, 'Wood Sword', 0, 1, True)
        return 'Wood Sword'

    async def rich_trophy_wipe(self, uid):
        await self.set_balance(uid, 0)
        await self.set_vault(uid, 0, 1)

        async with self.db.acquire() as con:
            await con.execute(
                'DELETE FROM items WHERE uid = $1 AND name != $2 AND name != $3',
                uid, 'Rich Person Trophy', 'Bane Of Pillagers Amulet'
            )

        self.uncache_user(uid)

    async def fetch_user_lb(self, uid):
        async with self.db.acquire() as con:
            lbs = await con.fetchrow('SELECT * FROM leaderboards WHERE uid = $1', uid)

            if lbs is None:
                await con.execute('INSERT INTO leaderboards VALUES ($1, $2, $3)', uid, 0, 0)

    async def update_lb(self, uid, lb, value, mode='add'):
        await self.fetch_user_lb(uid)

        if mode == 'add':
            async with self.db.acquire() as con:
                await con.execute(f'UPDATE leaderboards SET {lb} = {lb} + $1 WHERE uid = $2', value, uid)
        elif mode == 'sub':
            async with self.db.acquire() as con:
                await con.execute(f'UPDATE leaderboards SET {lb} = {lb} - $1 WHERE uid = $2', value, uid)
        elif mode == 'set':
            async with self.db.acquire() as con:
                await con.execute(f'UPDATE leaderboards SET {lb} = $1 WHERE uid = $2', value, uid)

    async def mass_fetch_leaderboard(self, lb):
        async with self.db.acquire() as con:
            return await con.fetch(f'SELECT uid, {lb} FROM leaderboards')

    async def set_botbanned(self, uid, botbanned):
        async with self.db.acquire() as con:
            await self.fetch_user(uid, con)

            if botbanned and uid not in self.d.ban_cache:
                self.d.ban_cache.append(uid)
            else:
                try:
                    self.d.ban_cache.pop(self.d.ban_cache.index(uid))
                except KeyError:
                    pass
                except ValueError:
                    pass

            await con.execute('UPDATE users SET bot_banned = $1 WHERE uid = $2', botbanned, uid)

        self.uncache_user(uid)

    async def add_warn(self, uid, gid, mod_id, reason):
        async with self.db.acquire() as con:
            await con.execute(
                'INSERT INTO warnings VALUES ($1, $2, $3, $4)',
                uid, gid, mod_id, reason
            )

    async def fetch_warns(self, uid, gid):
        async with self.db.acquire() as con:
            return await con.fetch('SELECT * FROM warnings WHERE uid = $1 AND gid = $2', uid, gid)

    async def clear_warns(self, uid, gid):
        async with self.db.acquire() as con:
            await con.execute('DELETE FROM warnings WHERE uid = $1 AND gid = $2', uid, gid)

    async def fetch_user_rcon(self, uid, mcserver):
        async with self.db.acquire() as con:
            return await con.fetchrow(
                'SELECT * FROM user_rcon WHERE uid = $1 AND mcserver = $2',
                uid, mcserver
            )

    async def add_user_rcon(self, uid, mcserver, rcon_port, password):
        async with self.db.acquire() as con:
            await con.execute(
                'INSERT INTO user_rcon VALUES ($1, $2, $3, $4)',
                uid, mcserver, rcon_port, password
            )

    async def delete_user_rcon(self, uid, mcserver):
        async with self.db.acquire() as con:
            await con.execute(
                'DELETE FROM user_rcon WHERE uid = $1 AND mcserver = $2',
                uid, mcserver
            )

    async def mass_delete_user_rcon(self, uid):
        async with self.db.acquire() as con:
            return await con.fetch('DELETE FROM user_rcon WHERE uid = $1 RETURNING *', uid)


def setup(bot):
    bot.add_cog(Database(bot))
