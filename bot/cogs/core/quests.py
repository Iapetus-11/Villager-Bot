import asyncio
import datetime
import math
import random
import typing
from dataclasses import dataclass

import arrow
import discord
from discord.ext import commands

from bot.utils.ctx import CustomContext
from bot.utils.misc import emojify_item, get_user_and_lang_from_loc, make_progress_bar
from bot.villager_bot import VillagerBotCluster
from common.models.data import Quest
from common.models.db.quests import UserQuest as DbUserQuest

if typing.TYPE_CHECKING:
    from bot.cogs.core.database import Database


class DailyQuestDoneView(discord.ui.View):
    def __init__(
        self,
        *,
        bot: VillagerBotCluster,
        loc: CustomContext | commands.Context | discord.User,
        user_id: int,
        timeout: float = 60.0,
    ):
        super().__init__(timeout=timeout)

        self._bot = bot
        self._loc = loc
        self._user_id = user_id

        self.message: discord.Message | None = None

    @property
    def _db(self) -> "Database":
        return typing.cast("Database", self._bot.get_cog("Database"))

    @property
    def _quests(self) -> "Quests":
        return typing.cast("Quests", self._bot.get_cog("Quests"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self._user_id

    @discord.ui.button(label="Get New Quest", style=discord.ButtonStyle.gray)
    async def btn_get_new_quest(self, interaction: discord.Interaction, button: discord.ui.Button):
        # TODO: This shit is cooked broua;odkfja;lkdfja;lkdjf;lskj
        _, lang = get_user_and_lang_from_loc(self._bot.l, self._loc)
        user = await self._db.fetch_user(self._user_id)

        if (arrow.now(datetime.timezone.utc) - user.last_dq_reroll).total_seconds() <= (60 * 30):
            await interaction.response.edit_message(
                embed=None,
                view=None,
                content=lang.econ.daily_quests.cant_reroll,
            )
            return

        await self._db.delete_user_daily_quest(self._user_id)
        await self._db.update_user(
            self._user_id, last_dq_reroll=datetime.datetime.now(datetime.timezone.utc)
        )

        quest = await self._quests.fetch_user_daily_quest(self._user_id)

        embed = self._quests.get_quest_embed(self._loc, quest)
        await interaction.response.edit_message(embed=embed, view=None)

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True

        await self.message.edit(view=self)


@dataclass(kw_only=True, frozen=True, slots=True)
class UserQuest:
    key: str
    value: int | float
    target_value: int | float
    acceptance_eval: str
    reward_item: str
    reward_amount: int
    emoji: str | None
    done: bool
    day: arrow.Arrow


class Quests(commands.Cog):
    def __init__(self, bot: VillagerBotCluster):
        self.bot = bot
        self.d = bot.d

    @property
    def db(self) -> "Database":
        return typing.cast("Database", self.bot.get_cog("Database"))

    def get_quest_embed(
        self, loc: CustomContext | commands.Context | discord.User, quest: UserQuest
    ):
        _, lang = get_user_and_lang_from_loc(self.bot.l, loc)

        quest_text = lang.econ.daily_quests.mapping[quest.key]
        quest_emoji = (
            emoji_getter := (
                lambda cur, path: emoji_getter(cur[path.pop(0)], path) if path else cur
            )
        )(self.d.emojis, quest.emoji.split("."))

        completion_percent: float = min(max((quest.value / quest.target_value) if quest.value else 0, 0), 1)
        close_to_completion = completion_percent > 0.75

        completion_bar = (
            make_progress_bar(
                self.d,
                completion_percent,
                10,
                (
                    "red"
                    if completion_percent < 0.4
                    else "purple"
                    if completion_percent < 0.75
                    else "green"
                ),
            )
            + "\n"
        )

        encouragements = (
            lang.econ.daily_quests.encouragements.done
            if quest.done
            else lang.econ.daily_quests.encouragements.close
            if close_to_completion
            else lang.econ.daily_quests.encouragements.far
        )

        title_message = (
            lang.econ.daily_quests.completed if quest.done else lang.econ.daily_quests.current
        )

        if quest.done:
            description = (
                completion_bar
                + "\n"
                + lang.econ.daily_quests.rewarded.format(
                    reward_amount=quest.reward_amount,
                    reward_emoji=emojify_item(self.d, quest.reward_item),
                )
            )
        else:
            description = "\n".join([
                completion_bar,
                lang.econ.daily_quests.progress.format(
                    progress=quest_text.progress.format(
                        value=quest.value,
                        target=quest.target_value,
                        encouragement=random.choice(encouragements),
                    ),
                ),
                lang.econ.daily_quests.reward.format(
                    reward_amount=quest.reward_amount,
                    reward_emoji=emojify_item(self.d, quest.reward_item),
                ),
                lang.econ.daily_quests.expires_at.format(
                    expires_at=discord.utils.format_dt(
                        quest.day.datetime + datetime.timedelta(days=1),
                        "R",
                    ),
                ),
            ])

        return discord.Embed(
            title=title_message.format(
                quest_title=quest_text.title.format(
                    target=quest.target_value,
                    emoji=quest_emoji,
                ),
            ),
            description=description,
            color=self.bot.embed_color,
        )

    async def get_random_quest_to_store(self, user_id: int) -> typing.TypedDict(
        "RandomQuest",
        {
            "key": str,
            "def": Quest,
            "variant_idx": int,
            "variant": Quest.TargetChoice,
            "difficulty_multi": float | None,
        },
    ):
        now = datetime.datetime.now(datetime.timezone.utc)

        user = await self.db.fetch_user(user_id)
        user_items = {item.name for item in await self.db.fetch_items(user_id)}

        pickaxe = await self.db.fetch_pickaxe(user_id)
        pickaxe_level = len(self.d.mining.pickaxes) - self.d.mining.pickaxes.index(pickaxe)

        quest_key: str = random.choice(list(self.d.normalized_quests.keys()))
        quest_def = self.d.normalized_quests[quest_key]
        while quest_def.requirements_eval is not None and not eval(
            quest_def.requirements_eval,
            {
                "user": user,
                "user_items": user_items,
                "now": now,
                "pickaxe": pickaxe,
                "pickaxe_level": pickaxe_level,
            },
        ):
            quest_key: str = random.choice(list(self.d.normalized_quests.keys()))
            quest_def = self.d.normalized_quests[quest_key]

        variant_idx = random.randint(0, len(quest_def.targets) - 1)
        variant = quest_def.targets[variant_idx]

        difficulty_multi = eval(
            quest_def.difficulty_eval_multi,
            {"pickaxe_level": pickaxe_level, "ceil": math.ceil},
            {},
        )

        return {
            "key": quest_key,
            "def": quest_def,
            "variant_idx": variant_idx,
            "variant": variant,
            "difficulty_multi": difficulty_multi,
        }

    async def quest_completed(
        self, loc: CustomContext | commands.Context | discord.User, quest: UserQuest
    ) -> None:
        user_id, _ = get_user_and_lang_from_loc(self.bot.l, loc)

        await asyncio.sleep(1.0 + random.randint(0, 2))

        await self.db.mark_daily_quest_as_done(user_id, quest.key)
        quest = await self.fetch_user_daily_quest(user_id)

        if quest.reward_item == "emerald":
            await self.db.balance_add(user_id, quest.reward_amount)
        elif quest.reward_item == "Barrel":
            await self.db.add_item(user_id, "Barrel", 1024, quest.reward_amount)
        else:
            raise NotImplementedError(f"Couldn't reward item {quest.reward_item} to user {user_id}")

        await self.db.update_lb(user_id, "daily_quests", 1)
        await self.db.update_lb(user_id, "week_daily_quests", 1)

        embed = self.get_quest_embed(loc, quest)
        view = DailyQuestDoneView(bot=self.bot, loc=loc, user_id=user_id)
        message = await loc.send(embed=embed, view=view)
        view.message = message

    async def notify_of_quest(
        self,
        loc: CustomContext | commands.Context | discord.User,
        quest: UserQuest,
    ) -> None:
        user_id, _ = get_user_and_lang_from_loc(self.bot.l, loc)

        await self.db.mark_daily_quest_as_notified(user_id, quest.key)

        embed = self.get_quest_embed(loc, quest)
        await loc.send(embed=embed)

    def _get_user_quest_from_db_quest(self, db_quest: DbUserQuest) -> UserQuest:
        quest_def = self.d.normalized_quests[db_quest["key"]]

        quest_target = quest_def.targets[db_quest["variant"]]

        if db_quest["difficulty_multi"] is not None:
            quest_target = Quest.TargetChoice(
                value=(quest_target.value * db_quest["difficulty_multi"]),
                reward=(quest_target.reward * db_quest["difficulty_multi"]),
            )

        return UserQuest(
            key=db_quest["key"],
            value=db_quest["value"],
            target_value=quest_target.value,
            acceptance_eval=quest_def.acceptance_eval,
            reward_item=db_quest["reward_item"],
            reward_amount=quest_target.reward,
            emoji=quest_def.emoji,
            done=db_quest["done"],
            day=db_quest["day"],
        )

    async def update_user_daily_quest(
        self,
        loc: CustomContext | commands.Context | discord.User,
        key: str,
        value: int | float,
        mode: typing.Literal["add", "set"] = "add",
    ) -> None:
        user_id, _ = get_user_and_lang_from_loc(self.bot.l, loc)

        db_quest = await self.db.update_user_daily_quest(user_id, key, value, mode)
        quest = self._get_user_quest_from_db_quest(db_quest)

        target_met = eval(
            quest.acceptance_eval, {"target": quest.target_value, "value": quest.value}
        )

        if target_met and not db_quest["done"]:
            asyncio.create_task(self.quest_completed(loc, quest))

        if not db_quest["notified"]:
            asyncio.create_task(self.notify_of_quest(loc, quest))

    async def fetch_user_daily_quest(self, user_id: int) -> UserQuest:
        db_quest = await self.db.fetch_user_daily_quest(user_id)

        return self._get_user_quest_from_db_quest(db_quest)


async def setup(bot: VillagerBotCluster) -> None:
    await bot.add_cog(Quests(bot))
