from contextlib import suppress

import arrow
import discord
from discord.ext import commands

from common.models.topgg_vote import TopggVote

from bot.cogs.core.database import Database
from bot.villager_bot import VillagerBotCluster


class Voting(commands.Cog):
    def __init__(self, bot: VillagerBotCluster):
        self.bot = bot
        self.d = bot.d
        self.logger = bot.logger.getChild("voting")

    @property
    def db(self) -> Database:
        return self.bot.get_cog("Database")

    async def vote(self, *, user_id: int, site: str, is_weekend: bool, is_test: bool, json: str):
        if 0 not in self.bot.shard_ids:
            return

        await self.bot.final_ready.wait()
        await self.bot.wait_until_ready()

        if is_test:
            self.logger.info(f"{site} webhooks test")
            await self.bot.error_channel.send(f"{site.upper()} WEBHOOKS TEST ```json\n{json}\n```")
            return

        self.logger.info(f"{user_id} voted on {site}")

        user = self.bot.get_user(user_id)

        if user is None:
            with suppress(discord.HTTPException):
                user = await self.bot.fetch_user(user_id)

        user_str = (
            "an unknown user" if user is None else discord.utils.escape_markdown(user.display_name)
        )

        await self.bot.vote_channel.send(f":tada::tada: **{user_str}** has voted! :tada::tada:")

        if user is None:
            return

        db_user = await self.db.fetch_user(user_id)

        last_vote = db_user.last_vote or 0
        vote_streak = (db_user.vote_streak or 0) + 1

        # make sure last vote wasn't within 12 hours
        if arrow.get(last_vote) > arrow.utcnow().shift(hours=-12):
            return

        # check if vote streak is expired
        if arrow.utcnow().shift(days=-1, hours=-12) > arrow.get(last_vote):  # vote streak expired
            vote_streak = 1

        await self.db.update_user(
            user_id, last_vote=arrow.utcnow().datetime, vote_streak=vote_streak
        )

        # determine emeralds reward
        if site == "top.gg":
            emeralds = self.d.topgg_reward

            if is_weekend:
                emeralds *= 2

            # higher the pickaxe, better the voting reward
            emeralds *= len(self.d.mining.pickaxes) - self.d.mining.pickaxes.index(
                await self.db.fetch_pickaxe(user_id)
            )

            # longer vote streak (up to 5 votes) the better the reward
            emeralds *= min(vote_streak, 5)
        else:
            raise NotImplementedError(f"No case for site {site}")

        if vote_streak is None:
            await self.db.balance_add(user_id, emeralds)
            await self.bot.send_embed(
                user,
                f"Thanks for voting! You've received **{emeralds}**{self.d.emojis.emerald}!",
                ignore_exceptions=True,
            )
        elif vote_streak % 16 == 0:
            barrels = max(int(vote_streak // 32 + 1), 8)
            await self.db.add_item(user.id, "Barrel", 1024, barrels)
            await self.bot.send_embed(
                user,
                f"Thanks for voting! You've received {barrels}x **Barrel**!",
                ignore_exceptions=True,
            )
        else:
            await self.db.balance_add(user_id, emeralds)
            await self.bot.send_embed(
                user,
                f"Thanks for voting! You've received **{emeralds}**{self.d.emojis.emerald}! (Vote streak is now {vote_streak})",
                ignore_exceptions=True,
            )

    @commands.Cog.listener()
    async def on_topgg_vote(self, vote: TopggVote):
        await self.vote(
            user_id=vote.user,
            site="top.gg",
            is_weekend=vote.isWeekend,
            is_test=(vote.type != "upvote"),
            json=vote.json(),
        )


async def setup(bot: VillagerBotCluster):
    await bot.add_cog(Voting(bot))
