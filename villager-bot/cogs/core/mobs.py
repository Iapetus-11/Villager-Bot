from discord.ext import commands
import classyjson as cj
import itertools
import asyncio
import discord
import random
import time
import math

from util.misc import make_health_bar


class MobSpawner:
    def __init__(self, bot):
        self.bot = bot

        self.d = bot.d
        self.db = bot.get_cog("Database")

    def engage_check(self, ctx):
        async def predicate(m):
            if m.channel != ctx.channel:
                return False

            if ctx.author.bot:
                return False

            if m.content.lower().lstrip(ctx.prefix) not in self.d.mobs_mech.valid_attacks:
                return False

            if ctx.author.id in self.bot.ban_cache:
                return False

            if (await self.ipc.eval(f"econ_paused_users.get({ctx.author.id})")).result is not None:
                return False

            return True

        return commands.check(predicate)

    def attack_check(self, ctx, engage_msg):
        def predicate(m):
            if (
                m.content.lower().lstrip(ctx.prefix) not in self.d.mobs_mech.valid_attacks
                and m.content.lower().lstrip(ctx.prefix) not in self.d.mobs_mech.valid_flees
            ):
                return False

            return m.channel == engage_msg.channel and m.author == engage_msg.author

        return commands.check(predicate)

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

    async def spawn_event(self, ctx):
        if ctx.guild is None:  # ignore dms
            return

        db_guild = await self.db.fetch_guild(ctx.guild.id)
        difficulty = db_guild["difficulty"]

        if difficulty == "peaceful":
            return

        difficulty_multi = 1.5 if difficulty == "hard" else 1

        # type of mob to be spawned
        mob_key = random.choice(tuple(self.d.mobs_mech.mobs))
        mob = cj.classify({**self.d.mobs_mech.mobs[mob_key].copy(), **ctx.l.mobs_mech.mobs[mob_key]})
        mob_max_health = mob.health

        await asyncio.sleep(random.random() * 3)

        # engage embed
        embed = discord.Embed(
            color=self.d.cc,
            title=f"**{random.choice(ctx.l.mobs_mech.mob_drops).format(mob.nice.lower())}**",
            description=ctx.l.mobs_mech.type_engage,
        )
        embed.set_image(url=mob.image)

        engage_msg = await ctx.send(embed=embed)

        # get the user who is going to be attacking the mob
        while True:
            try:
                initial_attack_msg = await self.bot.wait_for("message", check=self.engage_check(ctx), timeout=15)
            except asyncio.TimeoutError:
                await engage_msg.edit(suppress=True)
                return

            user = initial_attack_msg.author
            db_user = await self.db.fetch_user(user.id)
            user_health = db_user["health"]

            if user_health < 1:
                await self.bot.send_embed(ctx, ctx.l.mobs_mech.no_health)
                continue

            break

        await self.ipc.exec(f"econ_paused_users[{ctx.author.id}] = {time.time()}")

        async def free(new_user_health: int) -> None:
            await self.db.update_user(user.id, health=new_user_health)
            await self.ipc.eval(f"econ_paused_users.pop({ctx.author.id}, None)")  # unpause user

        # fetch user's sword, slime trophy, and suppress the engage message
        user_sword, slime_trophy, _ = await asyncio.gather(
            self.db.fetch_sword(user.id),
            self.db.fetch_item(user.id),
            engage_msg.edit(suppress=True),
        )

        for iteration in itertools.count(start=1):
            # create embed with mob image
            embed = discord.Embed(color=self.d.cc, title=ctx.l.mobs_mech.attack_or_flee)
            embed.set_image(url=mob.image)

            # add user health bar to embed
            embed.add_field(
                name=f"**{user.display_name}**",
                value=make_health_bar(
                    user_health, 20, self.d.emojis.heart_full, self.d.emojis.heart_half, self.d.emojis.heart_empty
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

            try:
                user_action_msg = await self.bot.wait_for("message", check=self.attack_check(ctx, engage_msg))
                user_action = user_action_msg.content.lower()
            except asyncio.TimeoutError:
                timed_out = True
            else:
                timed_out = False

            # check if user is a fucking baby
            if timed_out or user_action in self.d.mobs_mech.valid_flees:
                await fight_msg.edit(suppress=True)
                await free(user_health)
                await self.bot.send_embed(ctx, random.choice(ctx.l.mons_mech.flee_insults))

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
                await fight_msg.edit(suppress=True)
                await free(user_health)
                await self.bot.send_embed(
                    ctx, random.choice(ctx.l.mobs_mech.user_finishers).format(mob.nice.lower(), user_sword.lower())
                )

                break
            else:
                if mob_key == "baby_slime" and user_dmg == 0:  # say user missed the slime
                    await self.bot.send_embed(ctx, random.choice(mob.misses).format(user_sword.lower()))
                else:  # send regular attack message
                    await self.bot.send_embed(ctx, random.choice(ctx.l.mobs_mech.user_attacks).format(mob.nice.lower(), user_sword.lower()))
            
            async with ctx.typing():
                await asyncio.sleep(.75 + random.random() * 2)

            mob_dmg = random.randint(2, 6)
            
            if mob_key == "creeper": # add creeper mechanics
                if iteration > 2:
                    if random.choice((True, True, False)):  # creeper yeets your bloodied corpse across the map
                        user_health = 0

                        await fight_msg.edit(suppress=True)
                        await free(user_health)
                        await self.bot.send_embed(ctx, random.choice(mob.finishers))

                        break

                mob_dmg = 0

            user_health -= mob_dmg
            user_health = max(user_health, 0)
            
            if user_health < 1:  # you == noob
                await free(user_health)
                await self.bot.send_embed(ctx, random.choice(mob.finishers))
            else:
                await self.bot.send_embed(ctx, random.choice(mob.attacks))

            async with ctx.typing():
                await asyncio.sleep(.75 + random.random() * 2)

            await fight_msg.edit(suppress=True)


def setup(bot):
    bot.add_cog(MobSpawner(bot))
