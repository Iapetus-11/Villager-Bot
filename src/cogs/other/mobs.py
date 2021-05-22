from discord.ext import commands, tasks
from util.misc import make_health_bar
import asyncio
import discord
import random
import arrow
import math

import util.cj as cj


class Mobs(commands.Cog):  # fuck I really don't want to work on this
    def __init__(self, bot):
        self.bot = bot

        self.d = bot.d
        self.v = bot.v

        self.db = bot.get_cog("Database")
        self.events = bot.get_cog("Events")

        self.spawn_events.start()
        self.clear_pauses.start()

    def cog_unload(self):
        self.spawn_events.cancel()
        self.clear_pauses.cancel()

    @tasks.loop(seconds=1)
    async def clear_pauses(self):
        for uid in list(self.v.pause_econ):
            if (arrow.utcnow() - self.v.pause_econ[uid]).seconds > 20:
                self.v.pause_econ.pop(uid, None)

        await asyncio.sleep(0)

    def engage_check(self, m, ctx):
        u = m.author

        if self.v.pause_econ.get(u.id):
            return False

        if m.content.lower().replace(ctx.prefix, "", 1) not in self.d.mobs_mech.valid_attacks:
            return False

        return m.channel.id == ctx.channel.id and not u.bot and u.id not in self.v.ban_cache

    def attack_check(self, m, e_msg, ctx):
        if (
            m.content.lower().replace(ctx.prefix, "", 1) not in self.d.mobs_mech.valid_attacks
            and m.content.lower() not in self.d.mobs_mech.valid_flees
        ):
            return False

        return m.channel.id == e_msg.channel.id and m.author.id == e_msg.author.id

    async def calc_sword_damage(self, uid, sword, diff_multi):
        sword = sword.lower()

        if sword == "netherite sword":
            dmg = random.randint(7, 10)
        elif sword == "diamond sword":
            dmg = random.randint(6, 7)
        elif sword == "gold sword":
            dmg = random.randint(4, 5)
        elif sword == "iron sword":
            dmg = random.randint(2, 4)
        elif sword == "stone sword":
            dmg = random.randint(1, 3)
        else:
            dmg = random.randint(1, 2)

        if await self.db.fetch_item(uid, "Sharpness II Book") is not None:
            dmg *= 1.5
        elif await self.db.fetch_item(uid, "Sharpness I Book") is not None:
            dmg *= 1.25

        if diff_multi > 1:
            dmg /= 1.3

        return math.ceil(dmg)

    async def spawn_event(self, ctx):
        try:
            await asyncio.sleep(random.randint(1, 200) / 100)

            if ctx.guild is None:
                return

            db_guild = await self.db.fetch_guild(ctx.guild.id)
            diff = db_guild["difficulty"]

            if diff == "peaceful":
                return

            # difficulty multiplier
            diff_multi = 1.5 if diff == "hard" else 1

            # type of mob that will be spawned, just a string
            mob_key = random.choice(list(self.d.mobs_mech.mobs))

            mob = self.d.mobs_mech.mobs[mob_key].copy()
            mob.update(ctx.l.mobs_mech.mobs[mob_key])
            mob = cj.classify(mob)

            embed = discord.Embed(
                color=self.d.cc,
                title=f"**{random.choice(ctx.l.mobs_mech.mob_drops).format(mob.nice.lower())}**",
                description=ctx.l.mobs_mech.type_engage,  # fight it you little baby
            )

            embed.set_image(url=mob.image)

            embed_msg = await ctx.send(embed=embed)

            while True:
                try:
                    engage_msg = await self.bot.wait_for("message", check=(lambda m: self.engage_check(m, ctx)), timeout=15)
                except asyncio.TimeoutError:
                    await embed_msg.edit(suppress=True)
                    return

                u = engage_msg.author

                if self.v.pause_econ.get(u.id):
                    continue

                u_db = await self.db.fetch_user(u.id)

                if u_db["health"] < 2:
                    await self.bot.send(ctx, ctx.l.mobs_mech.no_health)
                else:
                    break

            await embed_msg.edit(suppress=True)

            u_sword = await self.db.fetch_sword(u.id)
            slime_trophy = await self.db.fetch_item(u.id, "Slime Trophy")

            # used later on to clear pause_econ based on who's been in there for tooo long
            self.v.pause_econ[u.id] = arrow.utcnow()

            u_health = u_db["health"]
            mob_max_health = mob.health

            iteration = 0

            while True:
                iteration += 1

                embed = discord.Embed(color=self.d.cc, title=ctx.l.mobs_mech.attack_or_flee)
                embed.set_image(url=mob.image)

                embed.add_field(  # user health bar
                    name=f"**{u.display_name}**",
                    value=make_health_bar(
                        u_health, 20, self.d.emojis.heart_full, self.d.emojis.heart_half, self.d.emojis.heart_empty
                    ),
                    inline=False,
                )

                embed.add_field(  # mob health bar
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

                msg = await ctx.send(embed=embed)

                try:
                    resp = await self.bot.wait_for(
                        "message", check=(lambda m: self.attack_check(m, engage_msg, ctx)), timeout=15
                    )  # wait for response
                except asyncio.TimeoutError:  # user didn't respond
                    await msg.edit(suppress=True)

                    self.v.pause_econ.pop(u.id, None)
                    await self.db.update_user(u.id, "health", u_health)

                    await self.bot.send(ctx, random.choice(ctx.l.mobs_mech.flee_insults))

                    return

                # user decides to not fight mob anymore cause they a little baby
                if resp.content.lower() in self.d.mobs_mech.valid_flees:
                    await msg.edit(suppress=True)

                    self.v.pause_econ.pop(u.id, None)
                    await self.db.update_user(u.id, "health", u_health)

                    await self.bot.send(ctx, random.choice(ctx.l.mobs_mech.flee_insults))

                    return

                u_dmg = await self.calc_sword_damage(u.id, u_sword, diff_multi)  # calculate damage

                if mob_key == "baby_slime":
                    if iteration < 3 and slime_trophy is None:
                        u_dmg = 0
                    elif slime_trophy is not None and random.choice((True, False, False)):
                        u_dmg = 0
                    elif iteration >= 3 and random.choice((True, False)):
                        u_dmg = 0

                mob.health -= u_dmg

                if mob.health < 1:  # user wins
                    self.v.pause_econ.pop(u.id, None)
                    await self.bot.send(
                        ctx, random.choice(ctx.l.mobs_mech.user_finishers).format(mob.nice.lower(), u_sword.lower())
                    )
                    break
                else:
                    if mob_key == "baby_slime" and u_dmg == 0:
                        await self.bot.send(ctx, random.choice(mob.misses).format(u_sword.lower()))
                    else:
                        await self.bot.send(
                            ctx, random.choice(ctx.l.mobs_mech.user_attacks).format(mob.nice.lower(), u_sword.lower())
                        )  # user attack message

                await asyncio.sleep(1)

                m_dmg = random.randint(2, 6)

                if mob_key == "creeper":
                    if iteration > 2:
                        if random.choice((True, False, False)):
                            self.v.pause_econ.pop(u.id, None)

                            u_health = 0

                            await self.bot.send(ctx, random.choice(mob.finishers))
                            break

                    m_dmg = 0

                u_health -= m_dmg
                u_health = 0 if u_health < 0 else u_health

                if u_health < 1:  # mob wins
                    self.v.pause_econ.pop(u.id, None)
                    await self.bot.send(ctx, random.choice(mob.finishers))
                    break
                else:
                    await self.bot.send(ctx, random.choice(mob.attacks))

                await asyncio.sleep(1.75)

                await msg.edit(suppress=True)

            await msg.edit(suppress=True)  # remove old Message

            embed = discord.Embed(color=self.d.cc)  # create new embed which shows health to show that user has lost / won
            embed.set_image(url=mob.image)

            embed.add_field(  # user health bar
                name=f"**{u.display_name}**",
                value=make_health_bar(
                    (u_health if u_health >= 0 else 0),
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
                    (mob.health if mob.health >= 0 else 0),
                    mob_max_health,
                    self.d.emojis.heart_full,
                    self.d.emojis.heart_half,
                    self.d.emojis.heart_empty,
                ),
                inline=False,
            )

            await ctx.send(embed=embed)

            await self.db.update_user(u.id, "health", u_health)

            u_db = await self.db.fetch_user(u.id)
            u_bal = u_db["emeralds"]

            if u_health > 0:  # user win
                if mob_key != "baby_slime" or random.randint(0, 25) != 1:
                    if diff == "easy":  # copied this ~~meth~~ math from the old code idek what it does lmao
                        ems_won = (
                            int(u_bal * (1 / random.choice((3, 3.25, 3.5, 3.75, 4))))
                            if u_bal < 256
                            else int(512 * (1 / random.choice((3, 3.25, 3.5, 3.75, 4))))
                        )
                    else:  # diff hard
                        ems_won = (
                            int(u_bal * (1 / random.choice((1.75, 2, 2.25, 2.5))))
                            if u_bal < 256
                            else int(512 * (1 / random.choice((1.75, 2, 2.25, 2.5))))
                        )

                    ems_won = int((ems_won if ems_won > 0 else 1) * diff_multi)

                    if await self.db.fetch_item(u.id, "Looting II Book") is not None:
                        ems_won = int(ems_won * 1.75)
                    elif await self.db.fetch_item(u.id, "Looting I Book") is not None:
                        ems_won = int(ems_won * 1.25)

                    await self.db.balance_add(u.id, ems_won)
                    await self.db.update_lb(u.id, "mobs_killed", 1, "add")

                    await self.bot.send(ctx, random.choice(ctx.l.mobs_mech.found).format(ems_won, self.d.emojis.emerald))
                else:
                    if diff == "easy":
                        balls_won = random.randint(1, 10)
                    else:
                        balls_won = random.randint(1, 20)

                    if await self.db.fetch_item(u.id, "Looting II Book") is not None:
                        balls_won *= 1.5
                    elif await self.db.fetch_item(u.id, "Looting I Book") is not None:
                        balls_won *= 1.25
                    balls_won = round(balls_won)

                    await self.db.add_item(u.id, "Slime Ball", 5, balls_won, True)

                    await self.bot.send(ctx, random.choice(ctx.l.mobs_mech.found).format(balls_won, self.d.emojis.slimeball))
            else:  # mob win
                if diff == "easy":  # haha code copying go brrrrrrrrr
                    ems_lost = (
                        int(u_bal * (1 / (random.choice([3.05, 3.3, 3.55, 3.8]) + 0.3)))
                        if u_bal > 20
                        else random.randint(2, 4)
                    )
                else:  # diff hard
                    ems_lost = (
                        int(u_bal * (1 / (random.choice([1.45, 1.55, 1.65, 1.75]) + 0.3)))
                        if u_bal > 20
                        else random.randint(5, 9)
                    )

                ems_lost = await self.db.balance_sub(u.id, ems_lost)

                if mob_key == "creeper":
                    await self.bot.send(
                        ctx, random.choice(ctx.l.mobs_mech.lost.creeper).format(ems_lost, self.d.emojis.emerald)
                    )
                else:
                    await self.bot.send(
                        ctx,
                        random.choice(ctx.l.mobs_mech.lost.normal).format(mob.nice.lower(), ems_lost, self.d.emojis.emerald),
                    )
        except Exception as e:
            await self.events.debug_error(ctx, e)

    @tasks.loop(seconds=0.05)
    async def spawn_events(self):
        for ctx in list(self.v.spawn_queue):
            self.v.spawn_queue.pop(ctx)
            self.bot.loop.create_task(self.spawn_event(ctx))  # ah yes eficeicncy


def setup(bot):
    bot.add_cog(Mobs(bot))
