from discord.ext import commands
from datetime import datetime
from typing import List, Set
import asyncio
import asyncpg


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = bot.d
        self.db = bot.db  # the asyncpg pool

        asyncio.create_task(self.populate_caches())

    @property
    def badges(self):
        return self.bot.get_cog("Badges")

    async def populate_caches(self):  # initial caches for speeeeeed
        # caches which need to be maintained cross-process *regardless*
        self.bot.ban_cache = await self.fetch_all_botbans()

        # per-guild caches, should only load settings for guilds the process can actually see
        self.bot.language_cache = await self.fetch_all_guild_langs()
        self.bot.prefix_cache = await self.fetch_all_guild_prefixes()
        self.bot.disabled_commands = await self.fetch_all_disabled_commands()
        self.bot.replies_cache = await self.fetch_all_do_replies()

    async def fetch_current_reminders(self) -> List[asyncpg.Record]:
        return await self.db.fetch("DELETE FROM reminders WHERE at <= $1 RETURNING *", datetime.utcnow())

    async def fetch_user_reminder_count(self, user_id: int) -> int:
        return await self.db.fetchval("SELECT COUNT(*) FROM reminders WHERE user_id = $1", user_id)

    async def add_reminder(self, user_id: int, channel_id: int, message_id: int, reminder: str, at: datetime) -> None:
        await self.db.execute(
            "INSERT INTO reminders (user_id, channel_id, message_id, reminder, at) VALUES ($1, $2, $3, $4, $5)",
            user_id,
            channel_id,
            message_id,
            reminder,
            at,
        )

    async def fetch_all_botbans(self) -> Set[int]:
        botban_records = await self.db.fetch("SELECT user_id FROM users WHERE bot_banned = true")
        return {r[0] for r in botban_records}

    async def fetch_all_guild_langs(self) -> dict:
        lang_records = await self.db.fetch(
            "SELECT guild_id, language FROM guilds WHERE language != $1 AND language != $2",
            "en",
            "en_us",
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
        replies_records = await self.db.fetch("SELECT guild_id FROM guilds WHERE do_replies = true")
        return {r[0] for r in replies_records}

    async def fetch_guild(self, guild_id: int) -> asyncpg.Record:
        g = await self.db.fetchrow("SELECT * FROM guilds WHERE guild_id = $1", guild_id)

        if g is None:
            await self.db.execute("INSERT INTO guilds (guild_id) VALUES ($1)", guild_id)

            return await self.fetch_guild(guild_id)

        return g

    async def set_guild_attr(self, guild_id: int, attr: str, value: object) -> None:
        await self.fetch_guild(guild_id)  # ensure it exists in db
        await self.db.execute(f"UPDATE guilds SET {attr} = $1 WHERE guild_id = $2", value, guild_id)

    async def drop_guild(self, guild_id: int) -> None:
        await self.db.execute("DELETE FROM guilds WHERE guild_id = $1", guild_id)

        try:
            del self.bot.lang_cache[guild_id]
        except KeyError:
            pass

        try:
            del self.bot.prefix_cache[guild_id]
        except KeyError:
            pass

    async def fetch_guild_premium(self, guild_id: int) -> bool:
        return bool(await self.db.fetchval("SELECT premium FROM guilds WHERE guild_id = $1", guild_id))

    async def set_cmd_usable(self, guild_id: int, command: str, usable: bool) -> None:
        if usable:
            await self.db.execute("DELETE FROM disabled_commands WHERE guild_id = $1 AND command = $2", guild_id, command)
        else:
            await self.db.execute("INSERT INTO disabled_commands (guild_id, command) VALUES ($1, $2)", guild_id, command)

    async def fetch_user(self, user_id: int) -> asyncpg.Record:
        user = await self.db.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)

        if user is None:
            await self.db.execute("INSERT INTO users (user_id) VALUES ($1)", user_id)

            await self.add_item(user_id, "Wood Pickaxe", 0, 1, True)
            await self.add_item(user_id, "Wood Sword", 0, 1, True)

            return await self.fetch_user(user_id)

        return user

    async def update_user(self, user_id: int, **kwargs) -> None:
        db_user = await self.fetch_user(user_id)  # ensures user exists + we use db_user for updating badges

        values = []
        sql = []

        for i, e in enumerate(kwargs.items()):
            k, v = e

            values.append(v)
            sql.append(f"{k} = ${i+1}")

        # this sql query crafting is safe because the user's input is still sanitized by asyncpg
        await self.db.execute(f"UPDATE users SET {','.join(sql)} WHERE user_id = ${i+2}", *values, user_id)

        # update badges
        await self.badges.update_badge_uncle_scrooge(user_id, db_user)

    async def fetch_balance(self, user_id: int) -> int:  # fetches the amount of emeralds a user has
        # we can do this because self.fetch_user ensures user is not None
        return (await self.fetch_user(user_id))["emeralds"]

    async def set_balance(self, user_id: int, emeralds: int) -> None:
        db_user = await self.fetch_user(user_id)  # ensures user exists + we use db_user for updating badges
        await self.db.execute("UPDATE users SET emeralds = $1 WHERE user_id = $2", emeralds, user_id)

        # update badges
        await self.badges.update_badge_uncle_scrooge(user_id, db_user)

    async def balance_add(self, user_id: int, amount: int) -> int:
        new_bal = await self.fetch_balance(user_id) + amount
        await self.set_balance(user_id, new_bal)
        return new_bal

    async def balance_sub(self, user_id: int, amount: int) -> int:
        bal = await self.fetch_balance(user_id)
        new = bal - amount

        if new < 0:
            amount = bal
            new = 0

        await self.set_balance(user_id, new)
        return amount

    async def fetch_vault(self, user_id: int) -> dict:  # fetches a user's vault in the form (vault_amount, vault_max)
        user = await self.fetch_user(user_id)
        return {"vault_bal": user["vault_bal"], 0: user["vault_bal"], "vault_max": user["vault_max"], 1: user["vault_max"]}

    async def set_vault(self, user_id: int, vault_balance: int, vault_max: int) -> None:
        db_user = await self.fetch_user(user_id)  # ensures user exists + we use db_user for updating badges
        await self.db.execute(
            "UPDATE users SET vault_balance = $1, vault_max = $2 WHERE user_id = $3", vault_balance, vault_max, user_id
        )

        # update badges
        await self.badges.update_badge_uncle_scrooge(user_id, db_user)

    async def fetch_items(self, user_id: int) -> List[asyncpg.Record]:
        await self.fetch_user(user_id)
        return await self.db.fetch("SELECT * FROM items WHERE user_id = $1", user_id)

    async def fetch_item(self, user_id: int, name: str) -> asyncpg.Record:
        await self.fetch_user(user_id)
        return await self.db.fetchrow("SELECT * FROM items WHERE user_id = $1 AND LOWER(name) = LOWER($2)", user_id, name)

    async def add_item(
        self, user_id: int, name: str, sell_price: int, amount: int, sticky: bool = False, sellable: bool = False
    ) -> None:
        prev = await self.fetch_item(user_id, name)

        if prev is None:
            await self.db.execute(
                "INSERT INTO items (user_id, name, sell_price, amount, sticky, sellable) VALUES ($1, $2, $3, $4, $5, $6)",
                user_id,
                name,
                sell_price,
                amount,
                sticky,
                sellable,
            )
        else:
            await self.db.execute(
                "UPDATE items SET amount = $1 WHERE user_id = $2 AND LOWER(name) = LOWER($3)",
                amount + prev["amount"],
                user_id,
                name,
            )

        # update badges
        await self.badges.update_badge_uncle_scrooge(user_id)
        await self.badges.update_badge_collector(user_id)

        if name == "Jar Of Bees":
            await self.badges.update_badge_beekeeper(user_id)

    async def remove_item(self, user_id: int, name: str, amount: int) -> None:
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

        # update badges
        await self.badges.update_badge_uncle_scrooge(user_id)

    async def log_transaction(self, item: str, amount: int, at: datetime, giver: int, receiver: int) -> None:
        await self.db.execute(
            "INSERT INTO give_logs (item, amount, at, sender, receiver) VALUES ($1, $2, $3, $4, $5)",
            item,
            amount,
            at,
            giver,
            receiver,
        )

    async def fetch_transactions_by_sender(self, user_id: int, limit: int) -> List[asyncpg.Record]:
        return await self.db.fetch("SELECT * FROM give_logs WHERE sender = $1 ORDER BY at DESC LIMIT $2", user_id, limit)

    async def fetch_transactions_page(self, user_id: int, limit: int = 10, *, page: int = 0) -> List[asyncpg.Record]:
        return await self.db.fetch(
            "SELECT * FROM give_logs WHERE sender = $1 OR receiver = $1 ORDER BY at DESC LIMIT $2 OFFSET $3",
            user_id,
            limit,
            page * limit,
        )

    async def fetch_transactions_page_count(self, user_id: int, limit: int = 10) -> int:
        return await self.db.fetchval("SELECT COUNT(*) FROM give_logs WHERE sender = $1 OR receiver = $1", user_id) // limit

    async def fetch_pickaxe(self, user_id: int) -> str:
        items_names = {item["name"] for item in await self.fetch_items(user_id)}

        for pickaxe in self.d.mining.pickaxes:
            if pickaxe in items_names:
                return pickaxe

            await asyncio.sleep(0)

        await self.add_item(user_id, "Wood Pickaxe", 0, 1, True)
        return "Wood Pickaxe"

    async def fetch_sword(self, user_id: int) -> str:
        items_names = {item["name"] for item in await self.fetch_items(user_id)}

        for sword in self.d.sword_list_proper:
            if sword in items_names:
                return sword

            await asyncio.sleep(0)

        await self.add_item(user_id, "Wood Sword", 0, 1, True)
        return "Wood Sword"

    async def rich_trophy_wipe(self, user_id: int) -> None:
        await self.set_balance(user_id, 0)
        await self.set_vault(user_id, 0, 1)

        await self.db.execute(
            "DELETE FROM items WHERE user_id = $1 AND NOT name = ANY($2::VARCHAR(250)[])",
            user_id,
            self.d.rpt_ignore,
        )

    async def fetch_user_lb(self, user_id: int) -> None:  # idk why this exists
        lbs = await self.db.fetchrow("SELECT * FROM leaderboards WHERE user_id = $1", user_id)

        if lbs is None:
            await self.db.execute("INSERT INTO leaderboards (user_id) VALUES ($1)", user_id)

    async def update_lb(self, user_id: int, lb: str, value: int, mode: str = "add") -> None:
        user_lb = await self.fetch_user_lb(user_id)  # ensure lb entry exists + we need this for later

        if mode == "add":
            await self.db.execute(
                f"UPDATE leaderboards SET {lb} = {lb} + $1 WHERE user_id = $2 RETURNING {lb}", value, user_id
            )

            if lb == "pillaged_emeralds":
                await self.badges.update_badge_pillager(user_id, user_lb[lb] + value)
            elif lb == "mobs_killed":
                await self.badges.update_badge_murderer(user_id, user_lb[lb] + value)
            elif lb == "fish_fished":
                await self.badges.update_badge_fisherman(user_id, user_lb[lb] + value)
        elif mode == "sub":
            await self.db.execute(f"UPDATE leaderboards SET {lb} = {lb} - $1 WHERE user_id = $2", value, user_id)
        elif mode == "set":
            await self.db.execute(f"UPDATE leaderboards SET {lb} = $1 WHERE user_id = $2", value, user_id)

            if lb == "pillaged_emeralds":
                await self.badges.update_badge_pillager(user_id, value)
            elif lb == "mobs_killed":
                await self.badges.update_badge_murderer(user_id, value)
            elif lb == "fish_fished":
                await self.badges.update_badge_fisherman(user_id, value)

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

    async def set_botbanned(self, user_id: int, botbanned: bool) -> None:
        await self.fetch_user(user_id)

        if botbanned:
            if user_id not in self.bot.ban_cache:
                self.bot.ban_cache.add(user_id)
        else:
            try:
                self.bot.ban_cache.remove(user_id)
            except ValueError:
                pass

        await self.db.execute("UPDATE users SET bot_banned = $1 WHERE user_id = $2", botbanned, user_id)

    async def add_warn(self, user_id: int, guild_id: int, mod_id: int, reason: str) -> None:
        await self.db.execute(
            "INSERT INTO warnings (user_id, guild_id, mod_id, reason) VALUES ($1, $2, $3, $4)",
            user_id,
            guild_id,
            mod_id,
            reason,
        )

    async def fetch_warns(self, user_id: int, guild_id: int) -> List[asyncpg.Record]:
        return await self.db.fetch("SELECT * FROM warnings WHERE user_id = $1 AND guild_id = $2", user_id, guild_id)

    async def clear_warns(self, user_id: int, guild_id: int) -> None:
        await self.db.execute("DELETE FROM warnings WHERE user_id = $1 AND guild_id = $2", user_id, guild_id)

    async def fetch_user_rcon(self, user_id: int, mc_server: str) -> asyncpg.Record:
        return await self.db.fetchrow("SELECT * FROM user_rcon WHERE user_id = $1 AND mc_server = $2", user_id, mc_server)

    async def add_user_rcon(self, user_id: int, mc_server: str, rcon_port: int, password: str) -> None:
        await self.db.execute(
            "INSERT INTO user_rcon (user_id, mc_server, rcon_port, password) VALUES ($1, $2, $3, $4)",
            user_id,
            mc_server,
            rcon_port,
            password,
        )

    async def delete_user_rcon(self, user_id: int, mc_server: str) -> None:
        await self.db.execute("DELETE FROM user_rcon WHERE user_id = $1 AND mc_server = $2", user_id, mc_server)

    async def mass_delete_user_rcon(self, user_id: int) -> List[asyncpg.Record]:
        return await self.db.fetch("DELETE FROM user_rcon WHERE user_id = $1 RETURNING *", user_id)

    async def fetch_user_badges(self, user_id: int) -> asyncpg.Record:
        user_badges = await self.db.fetchrow("SELECT code_helper, translator, villager_og, supporter, uncle_scrooge, collector, beekeeper, pillager, murderer, enthusiast, fisherman FROM badges WHERE user_id = $1", user_id)

        if user_badges is None:
            await self.db.execute("INSERT INTO badges (user_id) VALUES ($1)", user_id)
            return await self.fetch_user_badges(user_id)

        return user_badges

    async def update_user_badges(self, user_id: int, **kwargs) -> None:
        await self.fetch_user_badges(user_id)

        values = []
        sql = []

        for i, e in enumerate(kwargs.items()):
            k, v = e

            values.append(v)
            sql.append(f"{k} = ${i+1}")

        # this sql query crafting is safe because the user's input is still sanitized by asyncpg
        await self.db.execute(f"UPDATE badges SET {','.join(sql)} WHERE user_id = ${i+2}", *values, user_id)


def setup(bot):
    bot.add_cog(Database(bot))
