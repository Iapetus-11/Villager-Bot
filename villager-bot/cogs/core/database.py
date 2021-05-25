from discord.ext import commands, tasks
from datetime import datetime
from typing import List, Set
import asyncio
import asyncpg
import arrow


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = bot.d
        self.v = bot.v

        self.db = bot.db  # the asyncpg pool

        bot.loop.create_task(self.populate_caches())

    async def populate_caches(self):  # initial caches for speeeeeed
        # caches which need to be maintained cross-process *regardless*
        self.bot.ban_cache = await self.fetch_all_botbans()

        # per-guild caches, should only load settings for guilds the process can actually see
        self.bot.language_cache = await self.fetch_all_guild_langs()
        self.bot.prefix_cache = await self.fetch_all_guild_prefixes()
        self.bot.disabled_commands = await self.fetch_all_disabled_commands()
        self.bot.replies_cache = await self.fetch_all_do_replies()

    async def fetch_current_reminders(self) -> List[asyncpg.Record]:
        return await self.db.fetch("DELETE FROM reminders WHERE at <= $1 RETURNING *", arrow.utcnow().timestamp())

    async def fetch_user_reminder_count(self, user_id: int) -> int:
        return await self.db.fetchval("SELECT COUNT(*) FROM reminders WHERE user_id = $1", user_id)

    async def add_reminder(self, user_id: int, channel_id: int, message_id: int, reminder: str, at: datetime) -> None:
        await self.db.execute("INSERT INTO reminders VALUES ($1, $2, $3, $4, $5)", user_id, channel_id, message_id, reminder, at)

    async def fetch_all_botbans(self) -> Set[int]:
        botban_records = await self.db.fetch("SELECT user_id FROM users WHERE bot_banned = true")
        return {r[0] for r in botban_records}

    async def fetch_all_guild_langs(self) -> dict:
        lang_records = await self.db.fetch(
            "SELECT guild_id, lang FROM guilds WHERE (NOT language <> '') AND language != $1 AND language != $2", "en", "en_us"
        )
        return {r[0]: r[1] for r in lang_records}

    async def fetch_all_guild_prefixes(self) -> dict:
        prefix_records = await self.db.fetch("SELECT guild_id, prefix FROM guilds WHERE prefix != $1", self.d.default_prefix)
        return {r[0]: r[1] for r in prefix_records}

    async def fetch_all_disabled_commands(self) -> dict:
        disabled_records = await self.db.fetch("SELECT * FROM disabled_commands")
        disabled = {}

        for guild_id, command in disabled_records:
            try:
                disabled[guild_id].add(command)
            except KeyError:
                disabled[guild_id] = {command}

        return disabled

    async def fetch_all_do_replies(self) -> set:
        replies_records = await self.db.fetch("SELECT guild_id FROM guilds WHERE replies = true")
        return {r[0] for r in replies_records}

    async def fetch_guild(self, guild_id) -> asyncpg.Record:
        g = await self.db.fetchrow("SELECT * FROM guilds WHERE guild_id = $1", guild_id)

        if g is None:
            await self.db.execute(
                "INSERT INTO guilds VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
                guild_id,
                self.d.default_prefix,
                True,
                "easy",
                "en",
                None,
                False,
                False,
            )

            return await self.fetch_guild(guild_id)

        return g

    async def set_guild_attr(self, guild_id, attr, value):
        await self.fetch_guild(guild_id)  # ensure it exists in db
        await self.db.execute(f"UPDATE guilds SET {attr} = $1 WHERE guild_id = $2", value, guild_id)

    async def drop_guild(self, guild_id):
        await self.db.execute("DELETE FROM guilds WHERE guild_id = $1", guild_id)

        try:
            del self.v.lang_cache[guild_id]
        except KeyError:
            pass

        try:
            del self.v.prefix_cache[guild_id]
        except KeyError:
            pass

    async def fetch_guild_premium(self, guild_id):
        return bool(await self.db.fetchval("SELECT premium FROM guilds WHERE guild_id = $1", guild_id))

    async def set_cmd_usable(self, guild_id, cmd, usable):
        if usable:
            await self.db.execute("DELETE FROM disabled WHERE guild_id = $1 AND cmd = $2", guild_id, cmd)
        else:
            await self.db.execute("INSERT INTO disabled VALUES ($1, $2)", guild_id, cmd)

    async def fetch_user(self, user_id):
        user = await self.db.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)

        if user is None:
            await self.db.execute(
                "INSERT INTO users VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)", user_id, 0, 0, 1, 20, False, 0, 0, False
            )

            await self.add_item(user_id, "Wood Pickaxe", 0, 1, True)
            await self.add_item(user_id, "Wood Sword", 0, 1, True)

            return await self.fetch_user(user_id)

        return user

    async def update_user(self, user_id, key, value):
        await self.fetch_user(user_id)
        await self.db.execute(f"UPDATE users SET {key} = $1 WHERE user_id = $2", value, user_id)

    async def fetch_balance(self, user_id):  # fetches the amount of emeralds a user has
        # we can do this because self.fetch_user ensures user is not None
        return (await self.fetch_user(user_id))["emeralds"]

    async def set_balance(self, user_id, emeralds):
        await self.fetch_user(user_id)
        await self.db.execute("UPDATE users SET emeralds = $1 WHERE user_id = $2", emeralds, user_id)

    async def balance_add(self, user_id, amount):
        new_bal = await self.fetch_balance(user_id) + amount
        await self.set_balance(user_id, new_bal)
        return new_bal

    async def balance_sub(self, user_id, amount):
        bal = await self.fetch_balance(user_id)
        new = bal - amount

        if new < 0:
            amount = bal
            new = 0

        await self.set_balance(user_id, new)
        return amount

    async def fetch_vault(self, user_id):  # fetches a user's vault in the form (vault_amount, vault_max)
        user = await self.fetch_user(user_id)
        return {"vault_bal": user["vault_bal"], 0: user["vault_bal"], "vault_max": user["vault_max"], 1: user["vault_max"]}

    async def set_vault(self, user_id: int, vault_balance: int, vault_max: int) -> None:
        await self.fetch_user(user_id)
        await self.db.execute(
            "UPDATE users SET vault_balance = $1, vault_max = $2 WHERE user_id = $3", vault_balance, vault_max, user_id
        )

    async def fetch_items(self, user_id: int):
        await self.fetch_user(user_id)
        return await self.db.fetch("SELECT * FROM items WHERE user_id = $1", user_id)

    async def fetch_item(self, user_id, name):
        await self.fetch_user(user_id)
        return await self.db.fetchrow("SELECT * FROM items WHERE user_id = $1 AND LOWER(name) = LOWER($2)", user_id, name)

    async def add_item(self, user_id, name, sell_price, amount, sticky=False):
        prev = await self.fetch_item(user_id, name)

        if prev is None:
            await self.db.execute("INSERT INTO items VALUES ($1, $2, $3, $4, $5)", user_id, name, sell_price, amount, sticky)
        else:
            await self.db.execute(
                "UPDATE items SET amount = $1 WHERE user_id = $2 AND LOWER(name) = LOWER($3)",
                amount + prev["amount"],
                user_id,
                name,
            )

    async def remove_item(self, user_id, name, amount):
        prev = await self.fetch_item(user_id, name)

        if prev["amount"] - amount < 1:
            await self.db.execute("DELETE FROM items WHERE user_id = $1 AND LOWER(name) = LOWER($2)", user_id, name)
        else:
            await self.db.execute(
                "UPDATE items SET amount = $1 WHERE user_id = $2 AND LOWER(name) = LOWER($3)",
                prev["amount"] - amount,
                user_id,
                name,
            )

    async def log_transaction(self, item, amount, timestamp, giver, receiver):
        await self.db.execute("INSERT INTO give_logs VALUES ($1, $2, $3, $4, $5)", item, amount, timestamp, giver, receiver)

    async def fetch_transactions_by_sender(self, user_id, limit):
        return await self.db.fetch(
            "SELECT * FROM give_logs WHERE giver_user_id = $1 ORDER BY ts DESC LIMIT $2", user_id, limit
        )

    async def fetch_transactions_page(self, user_id, limit: int = 10, *, page: int = 0) -> list:
        return await self.db.fetch(
            "SELECT * FROM give_logs WHERE giver_user_id = $1 OR recvr_user_id = $1 ORDER BY ts DESC LIMIT $2 OFFSET $3",
            user_id,
            limit,
            page * limit,
        )

    async def fetch_transactions_page_count(self, user_id, limit: int = 10) -> int:
        return (
            await self.db.fetchval("SELECT COUNT(*) FROM give_logs WHERE giver_user_id = $1 OR recvr_user_id = $1", user_id)
            // limit
        )

    async def fetch_pickaxe(self, user_id):
        items_names = [item["name"] for item in await self.fetch_items(user_id)]

        for pickaxe in self.d.mining.pickaxes:
            if pickaxe in items_names:
                return pickaxe

            await asyncio.sleep(0)

        await self.add_item(user_id, "Wood Pickaxe", 0, 1, True)
        return "Wood Pickaxe"

    async def fetch_sword(self, user_id):
        items_names = [item["name"] for item in await self.fetch_items(user_id)]

        for sword in self.d.sword_list_proper:
            if sword in items_names:
                return sword

            await asyncio.sleep(0)

        await self.add_item(user_id, "Wood Sword", 0, 1, True)
        return "Wood Sword"

    async def rich_trophy_wipe(self, user_id):
        await self.set_balance(user_id, 0)
        await self.set_vault(user_id, 0, 1)

        await self.db.execute(
            "DELETE FROM items WHERE user_id = $1 AND NOT name = ANY($2::VARCHAR(250)[])",
            user_id,
            self.d.rpt_ignore,
        )

    async def fetch_user_lb(self, user_id):
        lbs = await self.db.fetchrow("SELECT * FROM leaderboards WHERE user_id = $1", user_id)

        if lbs is None:
            await self.db.execute("INSERT INTO leaderboards VALUES ($1, $2, $3, $4)", user_id, 0, 0, 0)

    async def update_lb(self, user_id, lb, value, mode="add"):
        await self.fetch_user_lb(user_id)

        if mode == "add":
            await self.db.execute(f"UPDATE leaderboards SET {lb} = {lb} + $1 WHERE user_id = $2", value, user_id)
        elif mode == "sub":
            await self.db.execute(f"UPDATE leaderboards SET {lb} = {lb} - $1 WHERE user_id = $2", value, user_id)
        elif mode == "set":
            await self.db.execute(f"UPDATE leaderboards SET {lb} = $1 WHERE user_id = $2", value, user_id)

    async def fetch_global_lb(self, lb: str, user_id: int) -> tuple:
        return (
            await self.db.fetch(f"SELECT user_id, {lb}, ROW_NUMBER() OVER(ORDER BY {lb} DESC) AS ordered FROM leaderboards"),
            await self.db.fetchrow(
                f"SELECT * FROM (SELECT user_id, {lb}, ROW_NUMBER() OVER(ORDER BY {lb} DESC) AS ordered FROM leaderboards) AS leaderboard WHERE user_id = $1",
                user_id,
            ),
        )

    async def fetch_local_lb(self, lb: str, user_id: int, user_ids: list) -> tuple:
        return (
            await self.db.fetch(
                f"SELECT user_id, {lb}, ROW_NUMBER() OVER(ORDER BY {lb} DESC) AS ordered FROM leaderboards WHERE user_id = ANY($1::BIGINT[])",
                user_ids,
            ),
            await self.db.fetchrow(
                f"SELECT * FROM (SELECT user_id, {lb}, ROW_NUMBER() OVER(ORDER BY {lb} DESC) AS ordered FROM leaderboards WHERE user_id = ANY($2::BIGINT[])) AS leaderboard WHERE user_id = $1",
                user_id,
                user_ids,
            ),
        )

    async def fetch_global_lb_user(self, column: str, user_id: int) -> tuple:
        return (
            await self.db.fetch(
                "SELECT user_id, {0}, ROW_NUMBER() OVER(ORDER BY {0} DESC) AS ordered FROM users WHERE {0} > 0 AND bot_banned = false LIMIT 10".format(
                    column
                )
            ),
            await self.db.fetchrow(
                "SELECT * FROM (SELECT user_id, {0}, ROW_NUMBER() OVER(ORDER BY {0} DESC) AS ordered FROM users WHERE {0} > 0 AND bot_banned = false) AS leaderboard WHERE user_id = $1".format(
                    column
                ),
                user_id,
            ),
        )

    async def fetch_local_lb_user(self, column: str, user_id: int, user_ids: list) -> tuple:
        return (
            await self.db.fetch(
                "SELECT user_id, {0}, ROW_NUMBER() OVER(ORDER BY {0} DESC) AS ordered FROM users WHERE {0} > 0 AND bot_banned = false AND user_id = ANY($1::BIGINT[]) LIMIT 10".format(
                    column
                ),
                user_ids,
            ),
            await self.db.fetchrow(
                "SELECT * FROM (SELECT user_id, {0}, ROW_NUMBER() OVER(ORDER BY {0} DESC) AS ordered FROM users WHERE {0} > 0 AND bot_banned = false AND user_id = ANY($2::BIGINT[])) AS leaderboard WHERE user_id = $1".format(
                    column
                ),
                user_id,
                user_ids,
            ),
        )

    async def fetch_global_lb_item(self, item: str, user_id: int) -> tuple:
        return (
            await self.db.fetch(
                "SELECT user_id, amount, ROW_NUMBER() OVER(ORDER BY amount DESC) AS ordered FROM items WHERE LOWER(name) = LOWER($1) LIMIT 10",
                item,
            ),
            await self.db.fetchrow(
                "SELECT user_id, amount, ROW_NUMBER() OVER(ORDER BY amount DESC) AS ordered FROM items WHERE LOWER(name) = LOWER($1) AND user_id = $2",
                item,
                user_id,
            ),
        )

    async def fetch_local_lb_item(self, item: str, user_id: int, user_ids: list) -> tuple:
        return (
            await self.db.fetch(
                "SELECT user_id, amount, ROW_NUMBER() OVER(ORDER BY amount DESC) AS ordered FROM items WHERE user_id = ANY($2::BIGINT[]) AND LOWER(name) = LOWER($1) LIMIT 10",
                item,
                user_ids,
            ),
            await self.db.fetchrow(
                "SELECT * FROM (SELECT user_id, amount, ROW_NUMBER() OVER(ORDER BY amount DESC) AS ordered FROM items WHERE user_id = ANY($3::BIGINT[]) AND LOWER(name) = LOWER($1)) AS leaderboard WHERE user_id = $2",
                item,
                user_id,
                user_ids,
            ),
        )

    async def set_botbanned(self, user_id, botbanned):
        await self.fetch_user(user_id)

        if botbanned:
            if user_id not in self.v.ban_cache:
                self.v.ban_cache.add(user_id)
        else:
            try:
                self.v.ban_cache.remove(user_id)
            except ValueError:
                pass

        await self.db.execute("UPDATE users SET bot_banned = $1 WHERE user_id = $2", botbanned, user_id)

    async def add_warn(self, user_id, guild_id, mod_id, reason):
        await self.db.execute("INSERT INTO warnings VALUES ($1, $2, $3, $4)", user_id, guild_id, mod_id, reason)

    async def fetch_warns(self, user_id, guild_id):
        return await self.db.fetch("SELECT * FROM warnings WHERE user_id = $1 AND guild_id = $2", user_id, guild_id)

    async def clear_warns(self, user_id, guild_id):
        await self.db.execute("DELETE FROM warnings WHERE user_id = $1 AND guild_id = $2", user_id, guild_id)

    async def fetch_user_rcon(self, user_id, mcserver):
        return await self.db.fetchrow("SELECT * FROM user_rcon WHERE user_id = $1 AND mcserver = $2", user_id, mcserver)

    async def add_user_rcon(self, user_id, mcserver, rcon_port, password):
        await self.db.execute("INSERT INTO user_rcon VALUES ($1, $2, $3, $4)", user_id, mcserver, rcon_port, password)

    async def delete_user_rcon(self, user_id, mcserver):
        await self.db.execute("DELETE FROM user_rcon WHERE user_id = $1 AND mcserver = $2", user_id, mcserver)

    async def mass_delete_user_rcon(self, user_id):
        return await self.db.fetch("DELETE FROM user_rcon WHERE user_id = $1 RETURNING *", user_id)


def setup(bot):
    bot.add_cog(Database(bot))