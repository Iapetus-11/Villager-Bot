import typing
from contextlib import suppress

import arrow
import discord
from discord.ext import commands
from discord.utils import format_dt


from bot.cogs.core.database import Database
from bot.cogs.core.quests import Quests
from bot.utils.misc import get_user_and_lang_from_loc
from bot.villager_bot import VillagerBotCluster
from common.models.topgg_vote import TopggVote


class VoteReminderView(discord.ui.View):
    def __init__(
        self,
        *,
        bot: VillagerBotCluster,
        user: discord.User,
        user_id: int,
        timeout: float = 300.0,
    ):
        super().__init__(timeout=timeout)

        self._bot = bot
        self._user = user
        self._user_id = user_id

        self.message: discord.Message | None = None

    @property
    def _db(self) -> Database:
        return typing.cast(Database, self._bot.get_cog("Database"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self._user_id

    @discord.ui.button(label="Add Vote Reminder", style=discord.ButtonStyle.gray)
    async def btn_add_vote_reminder(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer(thinking=False)
        _, lang = get_user_and_lang_from_loc(self._bot.l, self._user)

        at = arrow.utcnow().shift(hours=12)
        await self._db.add_reminder(
            interaction.user.id,
            interaction.channel.id,
            interaction.message.id,
            f"[Vote]({self._bot.d.topgg}/vote) for Villager Bot",
            at.datetime,
        )

        await self._bot.send_embed(
            interaction.user,
            lang.useful.remind.remind.format(
                self._bot.d.emojis.yes,
                format_dt(at.datetime, style="R"),
            ),
        )

        await self.on_timeout()

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True

        await self.message.edit(view=self)


class Voting(commands.Cog):
    def __init__(self, bot: VillagerBotCluster):
        self.bot = bot
        self.d = bot.d
        self.logger = bot.logger.getChild("voting")

    @property
    def db(self) -> Database:
        return typing.cast(Database, self.bot.get_cog("Database"))

    @property
    def quests(self) -> Quests:
        return typing.cast(Quests, self.bot.get_cog("Quests"))

    async def vote(self, *, user_id: int, site: str, is_weekend: bool, is_test: bool, json: str):
        await self.bot.final_ready.wait()
        await self.bot.wait_until_ready()

        if is_test:
            self.logger.info(f"{site} webhooks test")
            await self.bot.error_channel.send(f"{site.upper()} WEBHOOKS TEST ```json\n{json}\n```")
            return

        self.logger.info(f"{user_id} voted on {site}")
        self.bot.session_votes += 1

        user = await self.bot.fetch_user(user_id)
        embed = discord.Embed(color=self.bot.embed_color)

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
            user_id,
            last_vote=arrow.utcnow().datetime,
            vote_streak=vote_streak,
        )

        await self.quests.update_user_daily_quest(user, "votes", 1)

        # determine emeralds reward
        if site == "top.gg":
            emeralds = self.d.topgg_reward

            if is_weekend:
                emeralds *= 2

            # higher the pickaxe, better the voting reward
            emeralds *= len(self.d.mining.pickaxes) - self.d.mining.pickaxes.index(
                await self.db.fetch_pickaxe(user_id),
            )

            # longer vote streak (up to 10 votes) the better the reward
            emeralds *= min(vote_streak, 10)
        else:
            raise NotImplementedError(f"No case for site {site}")

        view = VoteReminderView(bot=self.bot, loc=user, user_id=user.id)
        if vote_streak is None:
            await self.db.balance_add(user_id, emeralds)
            embed.description = (
                f"Thanks for voting! You've received **{emeralds}**{self.d.emojis.emerald}!",
            )
            message = await user.send(embed=embed, view=view)

        elif vote_streak % 16 == 0:
            barrels = min(int(vote_streak // 32 + 1), 8)
            await self.db.add_item(user.id, "Barrel", 1024, barrels)
            embed.description = f"Thanks for voting! You've received {barrels}x **Barrel**!"
            message = await user.send(embed=embed, view=view)

        else:
            await self.db.balance_add(user_id, emeralds)
            embed.description = (
                f"Thanks for voting! You've received **{emeralds}**{self.d.emojis.emerald}! "
                f"(Vote streak is now {vote_streak})"
            )
            message = await user.send(embed=embed, view=view)
        view.message = message

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
