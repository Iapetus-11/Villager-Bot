import io
import typing
from io import BytesIO

from discord.ext import commands
from PIL import Image

from bot.models.db.item import Item
from bot.models.db.user import User

from bot.cogs.core.database import Database
from bot.logic.users import calc_total_wealth
from bot.villager_bot import VillagerBotCluster


class Badges(commands.Cog):
    def __init__(self, bot: VillagerBotCluster):
        self.bot = bot

        self.d = bot.d

    @property
    def db(self) -> Database:
        return typing.cast(Database, self.bot.get_cog("Database"))

    async def fetch_user_badges(self, user_id) -> dict:
        return dict(await self.db.fetch_user_badges(user_id))

    async def update_user_badges(self, user_id, **kwargs):
        await self.db.update_user_badges(user_id, **kwargs)

    def emojify_badges(self, user_badges: dict) -> str:
        emojis = []

        for badge, value in dict(user_badges).items():
            if not value:
                continue

            emoji_entry = self.d.emojis.badges[badge]

            if isinstance(emoji_entry, list):
                emojis.append(emoji_entry[value - 1])
            else:
                emojis.append(emoji_entry)

        return " ".join(emojis)

    async def update_badge_uncle_scrooge(
        self,
        user_id: int,
        db_user: User | None = None,
        user_items: list[Item] | None = None,
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

    async def update_badge_collector(self, user_id: int, user_items: list[Item] | None = None) -> None:
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

    async def update_badge_beekeeper(self, user_id: int, bees: int | None = None) -> None:
        # levels are:
        # I -> 100 bees
        # II -> 1_000 bees
        # III -> 100_000 bees

        badges = await self.fetch_user_badges(user_id)
        beekeeper_level = badges["beekeeper"]

        if beekeeper_level == 3:
            return

        if bees is None:
            bees = await self.db.fetch_item(user_id, "Jar Of Bees")

            if bees is None:
                bees = 0
            else:
                bees = bees.amount

        if beekeeper_level < 3 and bees >= 100_000:
            await self.update_user_badges(user_id, beekeeper=3)
        elif beekeeper_level < 2 and bees >= 1000:
            await self.update_user_badges(user_id, beekeeper=2)
        elif beekeeper_level < 1 and bees >= 100:
            await self.update_user_badges(user_id, beekeeper=1)

    async def update_badge_pillager(self, user_id: int, pillaged_emeralds: int) -> None:
        # levels are:
        # I -> 100 emeralds stolen
        # II -> 1_000 emeralds stolen
        # III -> 100_000 emeralds stolen

        badges = await self.fetch_user_badges(user_id)
        pillager_level = badges["pillager"]

        if pillager_level == 3:
            return

        if pillager_level < 3 and pillaged_emeralds >= 100_000:
            await self.update_user_badges(user_id, pillager=3)
        elif pillager_level < 2 and pillaged_emeralds >= 1_000:
            await self.update_user_badges(user_id, pillager=2)
        elif pillager_level < 1 and pillaged_emeralds >= 100:
            await self.update_user_badges(user_id, pillager=1)

    async def update_badge_murderer(self, user_id: int, murders: int) -> None:
        # levels are:
        # I -> 100 mobs cruelly genocided
        # II -> 1_000 mobs cruelly genocided
        # III -> 10_000 mobs cruelly genocided

        badges = await self.fetch_user_badges(user_id)
        murderer_level = badges["murderer"]

        if murderer_level == 3:
            return

        if murderer_level < 3 and murders >= 10_000:
            await self.update_user_badges(user_id, murderer=3)
        elif murderer_level < 2 and murders >= 1_000:
            await self.update_user_badges(user_id, murderer=2)
        elif murderer_level < 1 and murders >= 100:
            await self.update_user_badges(user_id, murderer=1)

    async def update_badge_fisherman(self, user_id: int, fishies_fished: int) -> None:
        # levels are:
        # I -> 100 fishies fished (cod)
        # II -> 1_000 fishies fished (tropical)
        # III -> 10_000 fishies fished (rainbow trout)
        # IV -> 100_000 fishies fished (emerald)

        badges = await self.fetch_user_badges(user_id)
        fisherman_level = badges["fisherman"]

        if fisherman_level == 4:
            return

        if fisherman_level < 4 and fishies_fished >= 100_000:
            await self.update_user_badges(user_id, fisherman=4)
        elif fisherman_level < 3 and fishies_fished >= 10_000:
            await self.update_user_badges(user_id, fisherman=3)
        elif fisherman_level < 2 and fishies_fished >= 1_000:
            await self.update_user_badges(user_id, fisherman=2)
        elif fisherman_level < 1 and fishies_fished >= 100:
            await self.update_user_badges(user_id, fisherman=1)

    async def update_badge_enthusiast(self, user_id: int, commands_ran: int) -> None:
        # levels are:
        # I -> 10_000 commands ran
        # II -> 1_000_000 commands ran
        # III -> 100_000_000 commands ran

        badges = await self.fetch_user_badges(user_id)
        enthusiast_level = badges["enthusiast"]

        if enthusiast_level < 3 and commands_ran > 10_000:
            await self.update_user_badges(user_id, enthusiast=3)
        elif enthusiast_level < 2 and commands_ran > 1_000_000:
            await self.update_user_badges(user_id, enthusiast=2)
        elif enthusiast_level < 1 and commands_ran > 100_000_000:
            await self.update_user_badges(user_id, enthusiast=1)

    async def generate_badges_image(self, user_id: int) -> io.BytesIO | None:
        """
        Generates an image for a user's badges. Returns None if the user has no badges,
        otherwise a BytesIO object containing the image's data.
        """

        user_badges = [
            f"{badge}_{'' if isinstance(value, bool) else value}".strip("_")
            for badge, value in (await self.fetch_user_badges(user_id)).items()
            if value is True or value > 0
        ]

        if not user_badges:
            return None

        badge_images = [
            (
                Image.open(f"./bot/data/assets/images/badges/{badge_name}.png").resize(
                    (100, 100),
                    resample=Image.Resampling.BICUBIC,
                )
            )
            for badge_name in user_badges
        ]

        total_width = max(1000, sum(image.width for image in badge_images))
        max_height = max(image.height for image in badge_images)

        badges_image = Image.new("RGBA", (total_width, max_height))

        current_x_pos = 0
        for image in badge_images:
            badges_image.paste(image, (current_x_pos, 0))
            current_x_pos += image.width

        img_bytes = BytesIO()
        badges_image.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        return img_bytes


async def setup(bot: VillagerBotCluster) -> None:
    await bot.add_cog(Badges(bot))
