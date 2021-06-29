from discord.ext import commands
from typing import List
import asyncpg

from util.misc import calc_total_wealth


class Badges(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.db = bot.get_cog("Database")

        self.badges = {}  # {user_id: {badge: value}}

    async def fetch_user_badges(self, user_id) -> dict:
        badges = self.badges.get(user_id)

        if badges is None:
            self.badges[user_id] = badges = await self.db.fetch_user_badges(user_id)

        return badges

    async def update_user_badges(self, user_id, **kwargs):
        badges = await self.fetch_user_badges(user_id)

        for badge, value in kwargs.items():
            badges[badge] = value

        await self.db.update_user_badges(user_id, **kwargs)

    async def update_badge_uncle_scrooge(
        self, user_id: int, db_user: asyncpg.Record, user_items: List[asyncpg.Record] = None
    ) -> None:
        badges = await self.fetch_user_badges(user_id)

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

        badges = await self.fetch_user_badges(user_id)

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

    async def update_badge_beekeeper(self, user_id: int, bees: int = None) -> None:
        # levels are:
        # I -> 100 bees
        # II -> 1000 bees
        # III -> 100000 bees

        badges = await self.fetch_user_badges(user_id)

        beekeeper_level = badges["beekeeper"]

        if beekeeper_level == 3:
            return

        if bees is None:
            bees = await self.db.fetch_item(user_id, "Jar Of Bees")

            if bees is None:
                bees = 0
            else:
                bees = bees["amount"]

        if beekeeper_level < 3 and bees >= 100_000:
            await self.update_user_badges(user_id, beekeeper=3)
        elif beekeeper_level < 2 and bees >= 1000:
            await self.update_user_badges(user_id, beekeeper=2)
        elif beekeeper_level < 1 and bees >= 100:
            await self.update_user_badges(user_id, beekeeper=1)

    async def update_badge_pillager(self, user_id: int, pillaged_emeralds: int) -> None:
        # levels are:
        # I -> 100 emeralds stolen
        # II -> 1000 emeralds stolen
        # III -> 100000 emeralds stolen

        badges = await self.fetch_user_badges(user_id)

        pillager_level = badges["pillager"]

        if pillager_level == 3:
            return

        if pillager_level < 3 and pillaged_emeralds >= 100_000:
            await self.update_user_badges(user_id, pillager=3)
        elif pillager_level < 2 and pillaged_emeralds >= 1000:
            await self.update_user_badges(user_id, pillager=2)
        elif pillager_level < 1 and pillaged_emeralds >= 100:
            await self.update_user_badges(user_id, pillager=1)

    async def update_badge_murderer(self, user_id: int, murders: int) -> None:
        # levels are:
        # I -> 100 mobs cruelly genocided
        # II -> 1000 mobs cruelly genocided
        # III -> 100000 mobs cruelly genocided

        badges = await self.fetch_user_badges(user_id)

        murderer_level = badges["pillager"]

        if murderer_level == 3:
            return

        if murderer_level < 3 and murders >= 100_000:
            await self.update_user_badges(user_id, murders=3)
        elif murderer_level < 2 and murders >= 1000:
            await self.update_user_badges(user_id, murders=2)
        elif murderer_level < 1 and murders >= 100:
            await self.update_user_badges(user_id, murders=1)




def setup(bot):
    bot.add_cog(Badges(bot))
