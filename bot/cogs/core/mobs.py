import asyncio
import itertools
import math
import random

import classyjson as cj
import discord
from bot.cogs.core.database import Database
from discord.ext import commands

from bot.utils.ctx import Ctx
from bot.utils.misc import SuppressCtxManager, make_health_bar
from bot.villager_bot import VillagerBotCluster


class MobSpawner(commands.Cog):
    def __init__(self, bot: VillagerBotCluster):
        self.bot = bot

        self.d = bot.d
        self.db: Database = bot.get_cog("Database")
        self.karen = bot.karen

    def engage_check(self, ctx: Ctx):
        def _engage_check(m: discord.Message):
            if m.channel != ctx.channel:
                return False

            if ctx.author.bot:
                return False

            if m.content.lower().lstrip(ctx.prefix) not in self.d.mobs_mech.valid_attacks:
                return False

            if ctx.author.id in self.bot.botban_cache:
                return False

            return True

        return _engage_check

    def attack_check(self, ctx: Ctx, engage_msg):
        def _attack_check(m):
            if not (m.channel == engage_msg.channel and m.author == engage_msg.author):
                return False

            return (
                m.content.lower().lstrip(ctx.prefix.lower()) in self.d.mobs_mech.valid_attacks
                or m.content.lower().lstrip(ctx.prefix.lower()) in self.d.mobs_mech.valid_flees
            )

        return _attack_check

    async def calculate_sword_damage(self, user_id: int, sword: str, multi: float) -> int:
        if sword == "Netherite Sword":
            damage = random.randint(7, 10)
        elif sword == "Diamond Sword":
            damage = random.randint(6, 7)
        elif sword == "Gold Sword":
            damage = random.randint(4, 5)
        elif sword == "Iron Sword":
            damage = random.randint(2, 4)
        elif sword == "Stone Sword":
            damage = random.randint(1, 3)
        elif sword == "Wood Sword":
            damage = random.randint(1, 2)
        else:
            raise ValueError(f"{repr(sword)} is not a valid sword.")

        if await self.db.fetch_item(user_id, "Sharpness II Book") is not None:
            damage *= 1.5
        elif await self.db.fetch_item(user_id, "Sharpness I Book") is not None:
            damage *= 1.25

        if multi > 1:
            damage /= 1.3

        return math.ceil(damage)

    async def spawn_event(self, ctx: Ctx):
        try:
            await self._spawn_event(ctx)
        except Exception:
            await self.bot.get_cog("Events").on_error("mob_spawn", ctx)

    async def _spawn_event(self, ctx: Ctx):
        if ctx.guild is None:  # ignore dms
            return

        db_guild = await self.db.fetch_guild(ctx.guild.id)
        difficulty = db_guild.difficulty

        if difficulty == "peaceful":
            return

        difficulty_multi = 1.5 if difficulty == "hard" else 1

        # type of mob to be spawned
        mob_key = random.choice(tuple(self.d.mobs_mech.mobs))
        mob = cj.classify(
            {**self.d.mobs_mech.mobs[mob_key].copy(), **ctx.l.mobs_mech.mobs[mob_key]}
        )
        mob_max_health = mob.health

        await asyncio.sleep(random.random() * 3)

        # engage embed
        embed = discord.Embed(
            color=self.bot.embed_color,
            title=f"**{random.choice(ctx.l.mobs_mech.mob_drops).format(mob.nice.lower())}**",
            description=ctx.l.mobs_mech.type_engage,
        )
        embed.set_image(url=mob.image)

        engage_msg = await ctx.send(embed=embed)

        # get the user who is going to be attacking the mob
        while True:
            try:
                initial_attack_msg: discord.Message = await self.bot.wait_for(
                    "message", check=self.engage_check(ctx), timeout=15
                )
            except asyncio.TimeoutError:
                await engage_msg.edit(suppress_embeds=True)
                return

            user = initial_attack_msg.author

            if await self.karen.check_econ_paused(user.id):
                continue

            db_user = await self.db.fetch_user(user.id)
            user_health = db_user.health

            if user_health < 1:
                await ctx.send_embed(ctx.l.mobs_mech.no_health)
                continue

            break

        # fetch user's sword, slime trophy, and suppress the engage message
        user_sword, slime_trophy, _ = await asyncio.gather(
            self.db.fetch_sword(user.id),
            self.db.fetch_item(user.id, "Slime Trophy"),
            engage_msg.edit(suppress_embeds=True),
        )

        await self.karen.econ_pause(user.id)

        try:
            for iteration in itertools.count(start=1):

                # create embed with mob image
                embed = discord.Embed(
                    color=self.bot.embed_color, title=ctx.l.mobs_mech.attack_or_flee
                )
                embed.set_image(url=mob.image)

                # add user health bar to embed
                embed.add_field(
                    name=f"**{user.display_name}**",
                    value=make_health_bar(
                        user_health,
                        20,
                        self.d.emojis.heart_full,
                        self.d.emojis.heart_half,
                        self.d.emojis.heart_empty,
                    ),
                    inline=False,
                )

                # add mob health bar to embed
                embed.add_field(
                    name=f"**{mob.nice}**",
                    value=make_health_bar(
                        mob.health,
                        mob_max_health,
                        self.d.emojis.heart_full,
                        self.d.emojis.heart_half,
                        self.d.emojis.heart_empty,
                    ),
                    inline=False,
                )

                fight_msg = await ctx.send(embed=embed)
                user_action: str = None

                # listen for attack or flee message (or timeout)
                while user_action not in self.d.mobs_mech.valid_attacks:
                    try:
                        user_action_msg: discord.Message = await self.bot.wait_for(
                            "message", check=self.attack_check(ctx, initial_attack_msg), timeout=30
                        )
                        user_action = user_action_msg.content.lstrip(ctx.prefix).lower()
                    except asyncio.TimeoutError:
                        timed_out = True
                    else:
                        timed_out = False

                    # check if user is a fucking baby
                    if timed_out or user_action in self.d.mobs_mech.valid_flees:
                        await fight_msg.edit(suppress_embeds=True)
                        await ctx.send_embed(random.choice(ctx.l.mobs_mech.flee_insults))

                        return

                user_dmg = await self.calculate_sword_damage(user.id, user_sword, difficulty_multi)

                # bebe slime is godlike
                if mob_key == "baby_slime":
                    if iteration < 3 and slime_trophy is None:
                        user_dmg = 0
                    elif slime_trophy is not None and random.choice((True, False, False)):
                        user_dmg = 0
                    elif iteration >= 3 and random.choice((True, False)):
                        user_dmg = 0

                mob.health -= user_dmg

                if mob.health < 1:  # user wins
                    await fight_msg.edit(suppress_embeds=True)
                    await ctx.send_embed(
                        random.choice(ctx.l.mobs_mech.user_finishers).format(
                            mob.nice.lower(), user_sword.lower()
                        )
                    )

                    break
                else:
                    if mob_key == "baby_slime" and user_dmg == 0:  # say user missed the slime
                        await ctx.send_embed(random.choice(mob.misses).format(user_sword.lower()))
                    else:  # send regular attack message
                        await ctx.send_embed(
                            random.choice(ctx.l.mobs_mech.user_attacks).format(
                                mob.nice.lower(), user_sword.lower()
                            )
                        )

                async with SuppressCtxManager(ctx.typing()):
                    await asyncio.sleep(0.75 + random.random() * 2)

                mob_dmg = random.randint(2, 6)

                if mob_key == "creeper":  # add creeper mechanics
                    if iteration > 2:
                        if random.choice(
                            (True, True, False)
                        ):  # creeper yeets your bloodied corpse across the map
                            user_health = 0

                            await fight_msg.edit(suppress_embeds=True)
                            await ctx.send_embed(random.choice(mob.finishers))

                            break

                    mob_dmg = 0

                user_health -= mob_dmg
                user_health = max(user_health, 0)

                if user_health < 1:  # you == noob
                    await ctx.send_embed(random.choice(mob.finishers))
                    break
                else:
                    await ctx.send_embed(random.choice(mob.attacks))

                async with SuppressCtxManager(ctx.typing()):
                    await asyncio.sleep(0.75 + random.random() * 2)

                await fight_msg.edit(suppress_embeds=True)

            # outside of the for loop
            embed = discord.Embed(color=self.bot.embed_color)
            embed.set_image(url=mob.image)

            embed.add_field(  # user health bar
                name=f"**{user.display_name}**",
                value=make_health_bar(
                    max(user_health, 0),
                    20,
                    self.d.emojis.heart_full,
                    self.d.emojis.heart_half,
                    self.d.emojis.heart_empty,
                ),
                inline=False,
            )

            embed.add_field(  # mob health bar
                name=f"**{mob.nice}**",
                value=make_health_bar(
                    max(mob.health, 0),
                    mob_max_health,
                    self.d.emojis.heart_full,
                    self.d.emojis.heart_half,
                    self.d.emojis.heart_empty,
                ),
                inline=False,
            )

            await ctx.send(embed=embed)

            db_user = await self.db.fetch_user(user.id)
            user_bal = db_user.emeralds

            # calculate looting level
            looting_level = 0
            if await self.db.fetch_item(user.id, "Looting II Book") is not None:
                looting_level = 2
            elif await self.db.fetch_item(user.id, "Looting I Book") is not None:
                looting_level = 1

            if user_health > 0:  # user win
                # if mob is slime, determine if it drops slime balls (1/26 chance)
                if mob_key == "baby_slime" and random.randint(0, 25 - (looting_level * 4)) == 1:
                    if difficulty == "easy":
                        balls_won = random.randint(1, 10)
                    else:
                        balls_won = random.randint(1, 20)

                    # increase balls won depending on looting level
                    balls_won = round(balls_won * ({0: 1, 1: 1.25, 2: 1.5}[looting_level]))

                    await self.db.add_item(user.id, "Slime Ball", 5, balls_won, True)

                    await ctx.send_embed(
                        random.choice(ctx.l.mobs_mech.found).format(
                            balls_won, self.d.emojis.slimeball
                        )
                    )
                # if mob is skeleton determine if they should drop bone meal (1/16 chance)
                elif mob_key == "skeleton" and random.randint(0, 20 - (looting_level * 3)) == 1:
                    await self.db.add_item(user.id, "Bone Meal", 512, 1)

                    await ctx.send_embed(
                        random.choice(ctx.l.mobs_mech.found).format(1, self.d.emojis.bone_meal)
                    )
                # mob should just drop emeralds
                else:
                    # calculate emeralds won based off difficulty
                    if difficulty == "easy":
                        ems_won = (
                            int(user_bal * (1 / random.choice((3, 3.25, 3.5, 3.75, 4))))
                            if user_bal < 256
                            else int(512 * (1 / random.choice((3, 3.25, 3.5, 3.75, 4))))
                        )
                    else:  # difficulty hard
                        ems_won = (
                            int(user_bal * (1 / random.choice((1.75, 2, 2.25, 2.5))))
                            if user_bal < 256
                            else int(512 * (1 / random.choice((1.75, 2, 2.25, 2.5))))
                        )

                    ems_won = int((ems_won if ems_won > 0 else 1) * difficulty_multi)

                    # increase ems won depending on looting_level
                    ems_won = int(ems_won * ({0: 1, 1: 1.25, 2: 1.75}[looting_level]))

                    await self.db.balance_add(user.id, ems_won)
                    await self.db.update_lb(user.id, "mobs_killed", 1, "add")
                    await self.db.update_lb(user.id, "week_emeralds", 1, "add")

                    await ctx.send_embed(
                        random.choice(ctx.l.mobs_mech.found).format(ems_won, self.d.emojis.emerald)
                    )
            else:  # mob win
                # determine how many emeralds they lose based off difficulty
                if difficulty == "easy":
                    ems_lost = (
                        int(user_bal * (1 / (random.choice([3.05, 3.3, 3.55, 3.8]) + 0.3)))
                        if user_bal > 20
                        else random.randint(2, 4)
                    )
                else:  # difficulty hard
                    ems_lost = (
                        int(user_bal * (1 / (random.choice([1.45, 1.55, 1.65, 1.75]) + 0.3)))
                        if user_bal > 20
                        else random.randint(5, 9)
                    )

                ems_lost = await self.db.balance_sub(user.id, ems_lost)

                if mob_key == "creeper":
                    await ctx.send_embed(
                        random.choice(ctx.l.mobs_mech.lost.creeper).format(
                            ems_lost, self.d.emojis.emerald
                        )
                    )
                else:
                    await ctx.send_embed(
                        random.choice(ctx.l.mobs_mech.lost.normal).format(
                            mob.nice.lower(), ems_lost, self.d.emojis.emerald
                        )
                    )
        finally:
            await self.db.update_user(user.id, health=user_health)
            await self.karen.econ_unpause(user.id)


async def setup(bot: VillagerBotCluster) -> None:
    await bot.add_cog(MobSpawner(bot))
