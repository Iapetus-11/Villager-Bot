from discord.ext import commands
from typing import List
import asyncpg

from util.misc import calc_total_wealth


class Badges(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.db = bot.get_cog("Database")

        self.badges = {}  # {user_id: {badge: value}}

    async def update_user_badges(self, user_id, **kwargs):
        badges = self.badges.get(user_id)

        if badges is None:
            self.badges[user_id] = badges = await self.db.fetch_user_badges(user_id)

        for badge, value in kwargs.items():
            badges[badge] = value

        await self.db.update_user_badges(user_id, **kwargs)

    async def update_badge_uncle_scrooge(
        self, user_id: int, db_user: asyncpg.Record, user_items: List[asyncpg.Record] = None
    ) -> None:
        badges = self.badges.get(user_id)

        if badges is None:
            self.badges[user_id] = badges = dict(await self.db.fetch_user_badges(user_id))

        if badges["uncle_scrooge"]:
            return

        if user_items is None:
            user_items = await self.db.fetch_items(user_id)

        if db_user is None:
            db_user = await self.db.fetch_user(user_id)

        total_wealth = calc_total_wealth(db_user, user_items)

        if total_wealth > 100_000:
            await self.update_user_badges(user_id, uncle_scrooge=True)

    async def update_badge_collector(self, user_id: int, user_items: List[asyncpg.Record] = None) -> None:
        # Levels are:
        # I -> 16 unique items
        # II -> 32  ||
        # III -> 64 ||
        # IV -> 128 ||
        # V -> 256  ||

        badges = self.badges.get(user_id)

        if badges is None:
            self.badges[user_id] = badges = dict(await self.db.fetch_user_badges(user_id))

        collector_level = badges["collector"]

        if collector_level == 5:
            return

        if user_items is None:
            user_items = await self.db.fetch_items(user_id)

        user_items_len = len(user_items)

        if collector_level < 5 and user_items_len >= 256:
            await self.update_user_badges(user_id, collector=5)
        elif collector_level < 4 and user_items_len >= 128:
            await self.update_user_badges(user_id, collector=4)
        elif collector_level < 3 and user_items_len >= 64:
            await self.update_user_badges(user_id, collector=3)
        elif collector_level < 2 and user_items_len >= 32:
            await self.update_user_badges(user_id, collector=2)
        elif collector_level < 1 and user_items_len >= 16:
            await self.update_user_badges(user_id, collector=1)


def setup(bot):
    bot.add_cog(Badges(bot))
