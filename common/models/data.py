from functools import cached_property
from typing import Any, Generator

from pydantic import Field, HttpUrl

from common.models.base_model import BaseModel, ImmutableBaseModel
from common.utils.misc import today_within_date_range


class MobsMech(ImmutableBaseModel):
    class Mob(ImmutableBaseModel):
        nice: str
        health: int
        image: HttpUrl

    valid_attacks: set[str]
    valid_flees: set[str]
    mobs: dict[str, Mob]


class Findable(ImmutableBaseModel):
    item: str
    sell_price: int
    rarity: int
    sticky: bool
    tags: set[str]


class Mining(ImmutableBaseModel):
    finds: list[list[str]]
    find_values: dict[str, float]
    yields_enchant_items: dict[str, list[int]]  # extra emerald yield from enchantments
    yields_pickaxes: dict[str, list[int]]  # emerald yield from different pickaxes

    @cached_property
    def pickaxes(self) -> list[str]:
        return list(self.yields_pickaxes)[::-1]


class Fishing(ImmutableBaseModel):
    class Fish(BaseModel):
        name: str
        value: list[int] = Field(min_items=2, max_items=2)
        current: float | None
        rarity: int

    exponent: float
    fish: dict[str, Fish]

    @cached_property
    def fish_ids(self) -> list[str]:
        return list(self.fish.keys())

    @cached_property
    def fishing_weights(self) -> list[float]:
        return [(len(self.fish_ids) - f.rarity) ** self.exponent for f in self.fish.values()]


class ShopItem(ImmutableBaseModel):
    class DbEntry(ImmutableBaseModel):
        item: str
        sell_price: int
        sticky: bool

    cat: str
    buy_price: int
    db_entry: DbEntry
    requires: dict[str, Any]


class Emojis(ImmutableBaseModel):
    class FarmingEmojis(ImmutableBaseModel):
        growing: dict[str, str]
        normal: dict[str, str]
        seeds: dict[str, str]

    class FishEmojis(ImmutableBaseModel):
        cod: str
        salmon: str
        tropical_fish: str
        pufferfish: str
        rainbow_trout: str
        gold_fish: str
        emerald_fish: str

    class SquareEmojis(ImmutableBaseModel):
        blue: str
        purple: str
        red: str
        orange: str
        yellow: str
        green: str
        brown: str
        black: str

    class BadgeEmojis(ImmutableBaseModel):
        code_helper: str
        translator: str
        design_helper: str
        bug_smasher: str
        villager_og: str
        supporter: str
        uncle_scrooge: str
        collector: list[str]
        beekeeper: list[str]
        pillager: list[str]
        murderer: list[str]
        enthusiast: list[str]
        fisherman: list[str]

    class ProgressBarEmojis(ImmutableBaseModel):
        class ProgressBarSetEmojis(ImmutableBaseModel):
            left: str
            middle: str
            right: str

        empty: ProgressBarSetEmojis
        red: ProgressBarSetEmojis
        purple: ProgressBarSetEmojis
        green: ProgressBarSetEmojis

    emerald: str
    emerald_block: str
    online: str
    offline: str
    netherite: str
    yes: str
    no: str
    stevegun: str
    bee: str
    anibee: str
    heart_full: str
    heart_half: str
    heart_empty: str
    aniheart: str
    updoot: str
    downdoot: str
    slimeball: str
    totem: str
    netherite_sword_ench: str
    netherite_pickaxe_ench: str
    bounce: str
    anichest: str
    rainbow_shep: str
    rainbow_stud: str
    emerald_spinn: str
    heart_spin: str
    enchanted_book: str
    amogus: str
    heart_of_the_sea: str
    autistic_emerald: str
    present: str
    morbius: str
    glass_bottle: str
    wood_sword: str
    stone_sword: str
    iron_sword: str
    gold_sword: str
    diamond_sword: str
    netherite_sword: str
    wood_pick: str
    stone_pick: str
    iron_pick: str
    gold_pick: str
    diamond_pick: str
    netherite_pick: str
    wood_hoe: str
    stone_hoe: str
    iron_hoe: str
    gold_hoe: str
    diamond_hoe: str
    netherite_hoe: str
    fishing_rod: str
    air: str
    jar_of_bees: str
    honey_jar: str
    uno_reverse: str
    rusty_fishing_hook: str
    ticket: str
    barrel: str
    rock: str
    gun: str
    alien: str
    rainbow: str
    pride_flag: str
    bone_meal: str
    diamond: str
    recycle: str
    guacamole_sombrero: str
    dirt_block: str
    trophy: str
    aniloading: str
    ender_pearl: str
    chocolate_chip_cookie: str
    will_o_wisp: str
    time_pearl: str
    shield_pearl: str
    feather: str
    pilgrim_hat: str
    turkey_leg: str
    seaweed: str
    mask: str
    cornucopia: str
    rudolfs_red_nose: str
    christmas_tree: str
    inflatable_santa: str
    snow_globe: str
    santa_sack: str
    moon_dust: str
    item_box: str
    fake_box: str
    banana: str
    green_shell: str
    red_shell: str
    mushroom: str
    mega_mushroom: str
    golden_mushroom: str
    blue_shell: str
    bunny_ears: str
    golden_bunny_ears: str
    rainbow_easter_egg: str
    green_striped_easter_egg: str
    purple_striped_easter_egg: str
    blue_striped_easter_egg: str
    blue_dotted_easter_egg: str
    green_dotted_easter_egg: str
    purple_dotted_easter_egg: str
    purple_easter_egg: str
    green_easter_egg: str
    blue_easter_egg: str
    red_striped_easter_egg: str
    yellow_striped_easter_egg: str
    orange_striped_easter_egg: str
    red_dotted_easter_egg: str
    yellow_dotted_easter_egg: str
    orange_dotted_easter_egg: str
    orange_easter_egg: str
    yellow_easter_egg: str
    red_easter_egg: str
    rich_person_trophy: str
    fishing_trophy: str
    slime_trophy: str
    calendar: str
    worm: str
    red_firework_rocket: str
    blue_firework_rocket: str
    green_firework_rocket: str
    orange_firework_rocket: str
    purple_firework_rocket: str
    yellow_firework_rocket: str
    american_flag: str
    uncle_sams_hat: str
    hot_dog: str
    bomb: str
    firecracker: str
    scroll: str
    infernums_scroll: str
    farming: FarmingEmojis
    reees: list[str]
    fish: FishEmojis
    squares: SquareEmojis
    badges: BadgeEmojis
    numbers: list[str]
    progress_bar: ProgressBarEmojis


class Farming(ImmutableBaseModel):
    class FarmingEmojis(ImmutableBaseModel):
        growing: dict[str, str]

    emojis: FarmingEmojis
    emerald_yields: dict[str, int]
    crop_yields: dict[str, list[int]]
    crop_times: dict[str, str]
    max_plots: dict[str, int]
    name_map: dict[str, str]
    plantable: dict[str, str]


class BuildIdeas(ImmutableBaseModel):
    ideas: list[str]
    prefixes: list[str]


class FunLangs(ImmutableBaseModel):
    enchant: dict[str, str]
    villager: dict[str, str]
    vaporwave: dict[str, str]

    @cached_property
    def unenchant(self) -> dict[str, str]:
        return {v: k for k, v in self.enchant.items()}


class Quest(ImmutableBaseModel):
    class TargetChoice(ImmutableBaseModel):
        value: int | float
        reward: int

    class TargetRange(ImmutableBaseModel):
        start: int
        stop: int
        step: int
        reward_eval: str

    targets: list[TargetChoice] | TargetRange
    difficulty_eval_multi: str
    acceptance_eval: str
    requirements_eval: str | None = Field(default=None)
    reward_item: str
    emoji: str

    def normalize(self) -> "NormalizedQuest":
        targets: list[Quest.TargetChoice] = []
        if isinstance(self.targets, list):
            targets = self.targets
        else:
            for value in range(
                self.targets.start,
                self.targets.stop + self.targets.step,
                self.targets.step,
            ):
                reward = eval(self.targets.reward_eval)
                targets.append(Quest.TargetChoice(value=value, reward=reward))

        return NormalizedQuest(
            targets=targets,
            difficulty_eval_multi=self.difficulty_eval_multi,
            acceptance_eval=self.acceptance_eval,
            requirements_eval=self.requirements_eval,
            reward_item=self.reward_item,
            emoji=self.emoji,
        )


class NormalizedQuest(Quest):
    targets: list[Quest.TargetChoice]


class Data(ImmutableBaseModel):
    embed_color: str
    splash_logo: str
    support: str
    invite: str
    topgg: str
    github: str
    privacy_policy: str
    mob_chance: int
    tip_chance: int
    topgg_reward: int
    credit_users: dict[str, int]  # name: discord id
    upvote_emoji_image: str
    acceptable_prefix_chars: list[str]
    cooldown_rates: dict[str, float]  # command: cooldown
    concurrency_limited: set[str]
    role_mappings: dict[str, int]  # item: role id
    sword_list: list[str]
    sword_list_proper: list[str]
    hoe_list_proper: list[str]
    kills: list[str]
    hmms: list[str]
    mobs_mech: MobsMech
    mining: Mining
    fishing: Fishing
    shop_items: dict[str, ShopItem]
    findables: list[Findable]
    findable_seasons: dict[str, tuple[tuple[int, int], tuple[int, int]]]
    rpt_ignore: list[str]
    cats: dict[str, list[str]]
    emojis: Emojis
    emoji_items: dict[str, str]
    farming: Farming
    build_ideas: BuildIdeas
    owos: list[str]
    emojified: dict[str, str]
    fun_langs: FunLangs
    cursed_images: list[str]
    playing_list: list[str]
    font_urls: list[str]
    disabled_translations: set[str]
    quests: dict[str, Quest]

    @property
    def mining_findables(self) -> list[Findable]:
        return list(self.filter_findables("mine"))

    @property
    def fishing_findables(self) -> list[Findable]:
        return list(self.filter_findables("fish"))

    def filter_findables(
        self,
        tag: str,
        *,
        allow_disabled: bool = False,
        enable_seasons: bool = True,
    ) -> Generator[Findable, None, None]:
        """
        Returns all enabled findables from data.json

        The allow_disabled param, when True, includes "disabled" items.
        The seasons param, when True, filters out items which aren't "in season"
        """

        offline_seasons = {
            k for k, v in self.findable_seasons.items() if not today_within_date_range(v)
        }

        for findable in self.findables:
            if not allow_disabled and "disabled" in findable.tags:
                continue

            if tag not in findable.tags:
                continue

            if enable_seasons and offline_seasons.intersection(findable.tags):
                continue

            yield findable

    @cached_property
    def normalized_quests(self) -> dict[str, NormalizedQuest]:
        return {key: quest.normalize() for key, quest in self.quests.items()}
