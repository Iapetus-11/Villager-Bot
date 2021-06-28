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

    async def update_uncle_scrooge(
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


def setup(bot):
    bot.add_cog(Badges(bot))
