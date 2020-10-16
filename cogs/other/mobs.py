from discord.ext import commands
import classyjson as cj
import asyncio
import discord
import random
import arrow
import math


class Mobs(commands.Cog):  # fuck I really don't want to work on this
    def __init__(self, bot):
        self.bot = bot
        self.d = self.bot.d

        self.db = self.bot.get_cog('Database')
        self.events = self.bot.get_cog('Events')

        self.make_stat_bar = self.bot.get_cog('Econ').make_stat_bar

        self.bot.loop.create_task(self.spawn_events())

    def engage_check(self, m, ctx):
        u = m.author

        if self.d.pause_econ.get(u.id):
            return False

        if m.content.lower() not in self.d.mobs_mech.valid_attacks:
            return False

        return m.channel.id == ctx.channel.id and not u.bot and u.id not in self.d.ban_cache and u.id == ctx.author.id

    def attack_check(self, m, ctx):
        if m.content.lower() not in self.d.mobs_mech.valid_attacks:
            return False

        return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id

    async def calc_sword_damage(self, uid, sword, diff_multi):
        sword = sword.lower()

        if sword == 'netherite sword':
            dmg = random.randint(7, 10)
        elif sword == 'diamond sword':
            dmg = random.randint(6, 7)
        elif sword == 'gold sword':
            dmg = random.randint(4, 5)
        elif sword == 'iron sword':
            dmg = random.randint(2, 4)
        elif sword == 'stone sword':
            dmg = random.randint(1, 3)
        else:
            dmg = random.randint(1, 2)

        if await self.db.fetch_item(uid, 'Sharpness II Book') is not None:
            dmg *= 1.5
        elif await self.db.fetch_item(uid, 'Sharpness I Book') is not None:
            dmg *= 1.25

        if diff_multi > 1:
            dmg = dmg / 1.3

        return math.ceil(dmg)

    async def spawn_event(self, ctx):
        try:
            self.d.spawn_queue.pop(self.d.spawn_queue.index(ctx))

            if ctx.guild is None:
                return

            db_guild = await self.db.fetch_guild(ctx.guild.id)
            diff = db_guild['difficulty']

            if diff == 'peaceful':
                return

            # difficulty multiplier
            diff_multi = 1
            if diff == 'hard':
                diff_multi *= 1.5

            # type of mob that will be spawned, just a string
            mob_key = random.choice(list(self.d.mobs_mech.mobs))

            mob = self.d.mobs_mech.mobs[mob_key].copy()
            mob.update(ctx.l.mobs_mech.mobs[mob_key])
            mob = cj.classify(mob)

            embed = discord.Embed(
                color=self.d.cc,
                title=f'**{random.choice(ctx.l.mobs_mech.mob_drops).format(mob.nice).lower()}**',
                description='Do you want to `fight` the mob?'  # fight it you little baby
            )

            embed.set_image(url=mob.image)

            embed_msg = await ctx.send(embed=embed)

            while True:
                try:
                    engage_msg = await self.bot.wait_for('message', check=(lambda m: self.engage_check(m, ctx)), timeout=15)
                except asyncio.TimeoutError:
                    await embed_msg.edit(suppress=True)
                    return

                u = engage_msg.author
                u_db = await self.db.fetch_user(u.id)

                if u_db['health'] < 2:
                    await self.bot.send(ctx, ctx.l.mobs_mech.no_health)
                else:
                    break

            u_sword = await self.db.fetch_sword(u.id)

            self.d.pause_econ[u.id] = arrow.utcnow()  # used later on to clear pause_econ based on who's been in there for tooo long

            u_health = u_db['health']
            mob_max_health = mob.health

            iteration = 0

            while u_health > 0 and mob.health > 0:
                iteration += 1

                embed = discord.Embed(color=self.d.cc, title='Do you want to `attack` or `flee`?')
                embed.set_image(url=mob.image)

                embed.add_field(  # user health bar
                    name=f'**{u.display_name}**',
                    value=(await self.make_stat_bar(u_health, 20, 10, self.d.emojis.heart_full, self.d.emojis.heart_empty)),
                    inline=False
                )

                embed.add_field(  # mob health bar
                    name=f'**{mob.nice}**',
                    value=(await self.make_stat_bar(
                        mob.health, mob_max_health,
                        mob_max_health/2,
                        self.d.emojis.heart_full,
                        self.d.emojis.heart_empty
                        )
                    ),
                    inline=False
                )

                msg = await ctx.send(embed=embed)

                try:
                    resp = await self.bot.wait_for('message', check=(lambda m: self.attack_check(m, ctx)), timeout=15)  # wait for response
                except asyncio.TimeoutError:  # user didn't respond
                    await msg.edit(suppress=True)

                    self.d.pause_econ.pop(u.id)

                    await self.bot.send(ctx, random.choice(ctx.l.mobs_mech.flee_insults))

                    return

                if resp.content.lower() in ('flee', 'run away'):  # user decides to not fight mob anymore cause they a little baby
                    await msg.edit(suppress=True)

                    self.d.pause_econ.pop(u.id)

                    await self.bot.send(ctx, random.choice(ctx.l.mobs_mech.flee_insults))

                    return

                u_dmg = await self.calc_sword_damage(u.id, u_sword, diff_multi)  # calculate damage

                if mob_key == 'baby_slime':
                    if iteration <= 4:
                        u_dmg = 0
                    elif iteration > 4 and random.choice((True, False)):
                        u_dmg = 0

                mob.health -= u_dmg

                if mob_key == 'baby_slime' and m_dmg == 0:
                    await self.bot.send(ctx, random.choice(mob.misses).format(u_sword))
                else:
                    await self.bot.send(ctx, random.choice(ctx.l.mobs_mech.user_attacks).format(mob.nice, u_sword))  # user attack message

                if mob.health < 1:  # user wins
                    self.d.pause_econ.pop(u.id)
                    await self.bot.send(ctx, random.choice(ctx.l.mobs_mech.user_finishers).format(mob.nice, u_sword))
                    break

                await asyncio.sleep(1)

                m_dmg = random.choice((2, 4, 6,))

                if mob_key == 'creeper':
                    if iteration > 2:
                        if random.choice((True, False, False)):
                            u_health = 0
                            break

                    m_dmg = 0

                u_health -= m_dmg

                await self.bot.send(ctx, random.choice(mob.attacks))

                if u_health < 1:  # mob wins
                    self.d.pause_econ.pop(u.id)
                    await self.bot.send(ctx, random.choice(mob.finishers))
                    break

                await asyncio.sleep(1.75)

            await msg.edit(suppress=True)  # remove old Message

            embed = discord.Embed(color=self.d.cc)  # create new embed which shows health to show that user has lost / won
            embed.set_image(url=mob.image)

            embed.add_field(  # user health bar
                name=f'**{u.display_name}**',
                value=(await self.make_stat_bar(u_health, 20, 10, self.d.emojis.heart_full, self.d.emojis.heart_empty))
            )

            embed.add_field(  # mob health bar
                name=f'**{mob.nice}**',
                value=(await self.make_stat_bar(
                    mob.health, mob_max_health,
                    mob_max_health/2,
                    self.d.emojis.heart_full,
                    self.d.emojis.heart_empty
                    )
                )
            )

            await ctx.send(embed=embed)

            u_db = await self.db.fetch_user(u.id)
            u_bal = u_db['emeralds']

            if u_health > 0:  # user win
                if diff == 'easy':  # copied this ~~meth~~ math from the old code idek what it does lmao
                    ems_won = int(u_bal * (1 / random.choice((3, 3.25, 3.5, 3.75, 4)))) if u_bal < 256 else int(
                        512 * (1 / random.choice((3, 3.25, 3.5, 3.75, 4))))
                else:  # diff hard
                    ems_won = int(u_bal * (1 / random.choice((1.75, 2, 2.25, 2.5)))) if u_bal < 256 else int(
                        512 * (1 / random.choice((1.75, 2, 2.25, 2.5))))

                ems_won = int((ems_won if ems_won > 0 else 1) * diff_multi)

                await self.db.balance_add(u.id, ems_won)

                await self.bot.send(ctx, random.choice(ctx.l.mobs_mech.found).format(ems_won, self.d.emojis.emerald))
            else:  # mob win
                if diff == 'easy':  # haha code copying go brrrrrrrrr
                    ems_lost = int(u_bal * (1 / (random.choice([3.05, 3.3, 3.55, 3.8])+.3))) if u_bal > 10 else random.randint(2, 4)
                else:  # diff hard
                    ems_lost = int(u_bal * (1 / (random.choice([1.45, 1.55, 1.65, 1.75])+.3))) if u_bal > 10 else random.randint(5, 9)

                await self.db.balance_sub(u.id, ems_lost)

                if mob_key == 'creeper':
                    await self.bot.send(ctx, random.choice(ctx.l.mobs_mech.lose.creeper).format(ems_lost, self.d.emojis.emerald))
                else:
                    await self.bot.send(ctx, random.choice(ctx.l.mobs_mech.lose.normal).format(mob.nice, ems_lost, self.d.emojis.emerald))
        except Exception as e:
            await self.events.debug_error(ctx, e)

    async def spawn_events(self):
        while True:
            await asyncio.sleep(.05)  # don't fucking remove this or else
            for ctx in self.d.spawn_queue:
                self.bot.loop.create_task(self.spawn_event(ctx))  # ah yes eficeicncy

def setup(bot):
    bot.add_cog(Mobs(bot))
