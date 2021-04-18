from discord.ext import commands, tasks
import asyncio
import discord
import arrow


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = bot.d

        self.db = bot.db  # the asyncpg pool

        self.update_user_health.start()
        bot.loop.create_task(self.populate_caches())

        self._user_cache = {}  # {uid: Record(user)}
        self._items_cache = {}  # {uid: [Record(item), Record(item)]}

    def cog_unload(self):
        self.update_user_health.cancel()

    async def populate_caches(self):  # initial caches for speeeeeed
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

    def cache_items(self, uid, items):
        self._items_cache[uid] = items
        return items

    def uncache_items(self, uid):
        try:
            del self._items_cache[uid]
        except KeyError:
            pass

    @tasks.loop(seconds=32)
    async def update_user_health(self):
        uids = await self.db.fetch("UPDATE users SET health = health + 1 WHERE health < 20 RETURNING uid")

        for uid in uids:
            self.uncache_user(uid)
            await asyncio.sleep(0)

    async def fetch_current_reminders(self) -> list:
        return await self.db.fetch("DELETE FROM reminders WHERE at <= $1 RETURNING *", arrow.utcnow().timestamp())

    async def fetch_user_reminder_count(self, uid: int) -> int:
        return await self.db.fetchval("SELECT COUNT(*) FROM reminders WHERE uid = $1", uid)

    async def add_reminder(self, uid: int, cid: int, mid: int, reminder: str, at: int):
        await self.db.execute("INSERT INTO reminders VALUES ($1, $2, $3, $4, $5)", uid, mid, cid, reminder, at)

    async def fetch_all_botbans(self):
        botban_records = await self.db.fetch(
            "SELECT uid FROM users WHERE bot_banned = true"
        )  # returns [Record<uid=>, Record<uid=>,..]
        return [r[0] for r in botban_records]

    async def fetch_all_guild_langs(self):
        lang_records = await self.db.fetch("SELECT gid, lang FROM guilds")

        return dict(
            (r[0], r[1]) for r in lang_records if (r[1] != "en" and r[1] is not None and r[1] != "en_us")
        )  # needs to be a dict

    async def fetch_all_guild_prefixes(self):
        prefix_records = await self.db.fetch("SELECT gid, prefix FROM guilds")

        return dict(
            (r[0], r[1]) for r in prefix_records if (r[1] != self.d.default_prefix and r[1] is not None)
        )  # needs to be a dict

    async def fetch_all_mcservers(self):
        servers = await self.db.fetch("SELECT host, link FROM mcservers")

        return [(s["host"], s["link"]) for s in servers]

    async def fetch_all_disabled_commands(self):
        disabled = await self.db.fetch("SELECT * FROM disabled")

        disabled_nice = {}

        for entry in disabled:
            disabled_nice[entry["gid"]] = disabled_nice.get(entry["gid"], []) + [entry[1]]

        return disabled_nice

    async def fetch_guild(self, gid):
        g = await self.db.fetchrow("SELECT * FROM guilds WHERE gid = $1", gid)

        if g is None:
            await self.db.execute(
                "INSERT INTO guilds VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
                gid,
                self.d.default_prefix,
                True,
                "easy",
                "en",
                None,
                False,
                False,
            )

            return await self.fetch_guild(gid)

        return g

    async def set_guild_attr(self, gid, attr, value):
        await self.fetch_guild(gid)  # ensure it exists in db
        await self.db.execute(f"UPDATE guilds SET {attr} = $1 WHERE gid = $2", value, gid)

    async def drop_guild(self, gid):
        await self.db.execute("DELETE FROM guilds WHERE gid = $1", gid)

        try:
            del self.d.lang_cache[gid]
        except KeyError:
            pass

        try:
            del self.d.prefix_cache[gid]
        except KeyError:
            pass

    async def fetch_guild_premium(self, gid):
        return bool(await self.db.fetchval("SELECT premium FROM guilds WHERE gid = $1", gid))

    async def set_cmd_usable(self, gid, cmd, usable):
        if usable:
            await self.db.execute("DELETE FROM disabled WHERE gid = $1 AND cmd = $2", gid, cmd)
        else:
            await self.db.execute("INSERT INTO disabled VALUES ($1, $2)", gid, cmd)

    async def fetch_user(self, uid):
        try:
            return self._user_cache[uid]
        except KeyError:
            self.uncache_user(uid)

        user = await self.db.fetchrow("SELECT * FROM users WHERE uid = $1", uid)

        if user is None:
            await self.db.execute(
                "INSERT INTO users VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)", uid, 0, 0, 1, 20, False, 0, 0, False
            )

            await self.add_item(uid, "Wood Pickaxe", 0, 1, True)
            await self.add_item(uid, "Wood Sword", 0, 1, True)

            return await self.fetch_user(uid)

        return self.cache_user(uid, user)

    async def update_user(self, uid, key, value):
        await self.fetch_user(uid)
        await self.db.execute(f"UPDATE users SET {key} = $1 WHERE uid = $2", value, uid)

        self.uncache_user(uid)

    async def fetch_balance(self, uid):  # fetches the amount of emeralds a user has
        # we can do this because self.fetch_user ensures user is not None
        return (await self.fetch_user(uid))["emeralds"]

    async def set_balance(self, uid, emeralds):
        await self.fetch_user(uid)
        await self.db.execute("UPDATE users SET emeralds = $1 WHERE uid = $2", emeralds, uid)

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
        user = await self.fetch_user(uid)
        return {"vault_bal": user["vault_bal"], 0: user["vault_bal"], "vault_max": user["vault_max"], 1: user["vault_max"]}

    async def set_vault(self, uid, vault_bal, vault_max):
        await self.fetch_user(uid)
        await self.db.execute("UPDATE users SET vault_bal = $1, vault_max = $2 WHERE uid = $3", vault_bal, vault_max, uid)

        self.uncache_user(uid)

    async def fetch_items(self, uid):
        try:
            return self._items_cache[uid]
        except KeyError:
            pass

        await self.fetch_user(uid)
        return self.cache_items(uid, await self.db.fetch("SELECT * FROM items WHERE uid = $1", uid))

    async def fetch_item(self, uid, name):
        try:
            for item_record in self._items_cache[uid]:
                if name.lower() == item_record["name"].lower():
                    return item_record

                await asyncio.sleep(0)
        except KeyError:
            pass

        await self.fetch_user(uid)
        return await self.db.fetchrow("SELECT * FROM items WHERE uid = $1 AND LOWER(name) = LOWER($2)", uid, name)

    async def add_item(self, uid, name, sell_price, amount, sticky=False):
        prev = await self.fetch_item(uid, name)

        if prev is None:
            await self.db.execute("INSERT INTO items VALUES ($1, $2, $3, $4, $5)", uid, name, sell_price, amount, sticky)
        else:
            await self.db.execute(
                "UPDATE items SET amount = $1 WHERE uid = $2 AND LOWER(name) = LOWER($3)", amount + prev["amount"], uid, name
            )

        self.uncache_items(uid)

    async def remove_item(self, uid, name, amount):
        prev = await self.fetch_item(uid, name)

        if prev["amount"] - amount < 1:
            await self.db.execute("DELETE FROM items WHERE uid = $1 AND LOWER(name) = LOWER($2)", uid, name)
        else:
            await self.db.execute(
                "UPDATE items SET amount = $1 WHERE uid = $2 AND LOWER(name) = LOWER($3)", prev["amount"] - amount, uid, name
            )

        self.uncache_items(uid)

    async def log_transaction(self, item, amount, timestamp, giver, receiver):
        await self.db.execute("INSERT INTO give_logs VALUES ($1, $2, $3, $4, $5)", item, amount, timestamp, giver, receiver)

    async def fetch_transactions_by_sender(self, uid, limit):
        return await self.db.fetch("SELECT * FROM give_logs WHERE giver_uid = $1 ORDER BY ts DESC LIMIT $2", uid, limit)

    async def fetch_transactions_page(self, uid, limit: int = 10, *, page: int = 0) -> list:
        return await self.db.fetch(
            "SELECT * FROM give_logs WHERE giver_uid = $1 OR recvr_uid = $1 ORDER BY ts DESC LIMIT $2 OFFSET $3",
            uid,
            limit,
            page * limit,
        )

    async def fetch_transactions_page_count(self, uid, limit: int = 10) -> int:
        return await self.db.fetchval("SELECT COUNT(*) FROM give_logs WHERE giver_uid = $1 OR recvr_uid = $1", uid) // limit

    async def fetch_pickaxe(self, uid):
        items_names = [item["name"] for item in await self.fetch_items(uid)]

        for pickaxe in self.d.mining.pickaxes:
            if pickaxe in items_names:
                return pickaxe

            await asyncio.sleep(0)

        await self.add_item(uid, "Wood Pickaxe", 0, 1, True)
        return "Wood Pickaxe"

    async def fetch_sword(self, uid):
        items_names = [item["name"] for item in await self.fetch_items(uid)]

        for sword in ("Netherite Sword", "Diamond Sword", "Gold Sword", "Iron Sword", "Stone Sword", "Wood Sword"):
            if sword in items_names:
                return sword

            await asyncio.sleep(0)

        await self.add_item(uid, "Wood Sword", 0, 1, True)
        return "Wood Sword"

    async def rich_trophy_wipe(self, uid):
        await self.set_balance(uid, 0)
        await self.set_vault(uid, 0, 1)

        await self.db.execute(
            "DELETE FROM items WHERE uid = $1 AND NOT name = ANY($2::VARCHAR(250)[])",
            uid,
            self.d.rpt_ignore,
        )

        # self.uncache_user(uid) # done in set_balance() and set_vault()
        self.uncache_items(uid)

    async def fetch_user_lb(self, uid):
        lbs = await self.db.fetchrow("SELECT * FROM leaderboards WHERE uid = $1", uid)

        if lbs is None:
            await self.db.execute("INSERT INTO leaderboards VALUES ($1, $2, $3, $4)", uid, 0, 0, 0)

    async def update_lb(self, uid, lb, value, mode="add"):
        await self.fetch_user_lb(uid)

        if mode == "add":
            await self.db.execute(f"UPDATE leaderboards SET {lb} = {lb} + $1 WHERE uid = $2", value, uid)
        elif mode == "sub":
            await self.db.execute(f"UPDATE leaderboards SET {lb} = {lb} - $1 WHERE uid = $2", value, uid)
        elif mode == "set":
            await self.db.execute(f"UPDATE leaderboards SET {lb} = $1 WHERE uid = $2", value, uid)

    async def fetch_global_lb(self, lb: str, uid: int) -> tuple:
        return (
            await self.db.fetch(f"SELECT uid, {lb}, ROW_NUMBER() OVER(ORDER BY {lb} DESC) AS ordered FROM leaderboards"),
            await self.db.fetchrow(
                f"SELECT * FROM (SELECT uid, {lb}, ROW_NUMBER() OVER(ORDER BY {lb} DESC) AS ordered FROM leaderboards) AS leaderboard WHERE uid = $1",
                uid,
            ),
        )

    async def fetch_local_lb(self, lb: str, uid: int, uids: list) -> tuple:
        return (
            await self.db.fetch(
                f"SELECT uid, {lb}, ROW_NUMBER() OVER(ORDER BY {lb} DESC) AS ordered FROM leaderboards WHERE uid = ANY($1::BIGINT[])",
                uids,
            ),
            await self.db.fetchrow(
                f"SELECT * FROM (SELECT uid, {lb}, ROW_NUMBER() OVER(ORDER BY {lb} DESC) AS ordered FROM leaderboards WHERE uid = ANY($2::BIGINT[])) AS leaderboard WHERE uid = $1",
                uid,
                uids,
            ),
        )

    async def fetch_global_lb_user(self, column: str, uid: int) -> tuple:
        return (
            await self.db.fetch(
                "SELECT uid, {0}, ROW_NUMBER() OVER(ORDER BY {0} DESC) AS ordered FROM users WHERE {0} > 0 AND bot_banned = false LIMIT 10".format(
                    column
                )
            ),
            await self.db.fetchrow(
                "SELECT * FROM (SELECT uid, {0}, ROW_NUMBER() OVER(ORDER BY {0} DESC) AS ordered FROM users WHERE {0} > 0 AND bot_banned = false) AS leaderboard WHERE uid = $1".format(
                    column
                ),
                uid,
            ),
        )

    async def fetch_local_lb_user(self, column: str, uid: int, uids: list) -> tuple:
        return (
            await self.db.fetch(
                "SELECT uid, {0}, ROW_NUMBER() OVER(ORDER BY {0} DESC) AS ordered FROM users WHERE {0} > 0 AND bot_banned = false AND uid = ANY($1::BIGINT[]) LIMIT 10".format(
                    column
                ),
                uids,
            ),
            await self.db.fetchrow(
                "SELECT * FROM (SELECT uid, {0}, ROW_NUMBER() OVER(ORDER BY {0} DESC) AS ordered FROM users WHERE {0} > 0 AND bot_banned = false AND uid = ANY($2::BIGINT[])) AS leaderboard WHERE uid = $1".format(
                    column
                ),
                uid,
                uids,
            ),
        )

    async def fetch_global_lb_item(self, item: str, uid: int) -> tuple:
        return (
            await self.db.fetch(
                "SELECT uid, amount, ROW_NUMBER() OVER(ORDER BY amount DESC) AS ordered FROM items WHERE LOWER(name) = LOWER($1) LIMIT 10",
                item,
            ),
            await self.db.fetchrow(
                "SELECT uid, amount, ROW_NUMBER() OVER(ORDER BY amount DESC) AS ordered FROM items WHERE LOWER(name) = LOWER($1) AND uid = $2",
                item,
                uid,
            ),
        )

    async def fetch_local_lb_item(self, item: str, uid: int, uids: list) -> tuple:
        return (
            await self.db.fetch(
                "SELECT uid, amount, ROW_NUMBER() OVER(ORDER BY amount DESC) AS ordered FROM items WHERE uid = ANY($2::BIGINT[]) AND LOWER(name) = LOWER($1) LIMIT 10",
                item,
                uids,
            ),
            await self.db.fetchrow(
                "SELECT * FROM (SELECT uid, amount, ROW_NUMBER() OVER(ORDER BY amount DESC) AS ordered FROM items WHERE uid = ANY($3::BIGINT[]) AND LOWER(name) = LOWER($1)) AS leaderboard WHERE uid = $2",
                item,
                uid,
                uids,
            ),
        )

    async def set_botbanned(self, uid, botbanned):
        await self.fetch_user(uid)

        if botbanned:
            if uid not in self.d.ban_cache:
                self.d.ban_cache.append(uid)
        else:
            try:
                self.d.ban_cache.remove(uid)
            except ValueError:
                pass

        await self.db.execute("UPDATE users SET bot_banned = $1 WHERE uid = $2", botbanned, uid)

        self.uncache_user(uid)

    async def add_warn(self, uid, gid, mod_id, reason):
        await self.db.execute("INSERT INTO warnings VALUES ($1, $2, $3, $4)", uid, gid, mod_id, reason)

    async def fetch_warns(self, uid, gid):
        return await self.db.fetch("SELECT * FROM warnings WHERE uid = $1 AND gid = $2", uid, gid)

    async def clear_warns(self, uid, gid):
        await self.db.execute("DELETE FROM warnings WHERE uid = $1 AND gid = $2", uid, gid)

    async def fetch_user_rcon(self, uid, mcserver):
        return await self.db.fetchrow("SELECT * FROM user_rcon WHERE uid = $1 AND mcserver = $2", uid, mcserver)

    async def add_user_rcon(self, uid, mcserver, rcon_port, password):
        await self.db.execute("INSERT INTO user_rcon VALUES ($1, $2, $3, $4)", uid, mcserver, rcon_port, password)

    async def delete_user_rcon(self, uid, mcserver):
        await self.db.execute("DELETE FROM user_rcon WHERE uid = $1 AND mcserver = $2", uid, mcserver)

    async def mass_delete_user_rcon(self, uid):
        return await self.db.fetch("DELETE FROM user_rcon WHERE uid = $1 RETURNING *", uid)


def setup(bot):
    bot.add_cog(Database(bot))
