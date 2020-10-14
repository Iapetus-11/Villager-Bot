from discord.ext import commands
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

        self.bot.loop.create_task(self.spawn_events())

        self.make_stat_bar = self.bot.get_cog('Econ').make_stat_bar

    def engage_check(self, m, ctx):
        u = m.author

        if self.d.pause_econ.get(u.id):
            return False

        if m.content.lower() not in self.d.mobs_mech.valid_attacks:
            return False

        u_db = await self.db.fetch_user(u.id)

        if u_db['health'] < 2:
            await ctx.send('You don\'t have enough health to fight this mob!')
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
        self.d.spawn_queue.pop(self.d.spawn_queue.index(ctx))

        if ctx.guild is None:
            return

        db_guild = await self.d.fetch_guild(ctx.guild.id)
        diff = db_guild['difficulty']

        if diff == 'easy':
            return

        # difficulty multiplier
        diff_multi = 1
        if diff == 'hard':
            diff_multi *= 1.5

        # type of mob that will be spawned, just a string
        mob_key = random.choice(list(self.d.mobs_mech.mobs))

        mob = self.d.mobs_mech[mob_key].copy()
        mob.update(ctx.l.mobs_mech.mobs[mob_key])

        embed = discord.Embed(
            color=self.d.cc,
            title=f'**{random.choice(ctx.l.mobs_mech.mob_drops).format(mob.nice).lower()}**',
            description='Do you want to `fight` the mob?'  # fight it you little baby
        )

        embed.set_image(url=mob.image)

        embed_msg = await ctx.send(embed=embed)

        try:
            drop_announce = await self.bot.wait_for('message', check=(lambda m: self.engage_check(m, ctx)), timeout=15)
        except asyncio.TimeoutError:
            await drop_announce.edit(suppress=True)
            return

        u = drop_announce.author
        u_db = await self.db.fetch_user(u.id)
        u_sword = await self.db.fetch_sword(u.id)

        self.d.pause_econ[u.id] = arrow.utcnow()

        u_health = u_db['health']
        mob_max_health = self.d.mobs_mech.mobs[mob_key].health

        iteration = 0

        while u_health > 0 and mob.health > 0:
            iteration += 1

            embed = discord.Embed(color=self.d.cc, title='Do you want to `attack` or `flee`?')
            embed.set_image(url=mob.image)

            embed.add_field(
                name=f'**{u.display_name}**',
                value=(await self.make_stat_bar(u_health, 20, 10, self.d.emojis.heart_full, self.d.emojis.heart_empty))
            )

            embed.add_field(
                name=f'**{mob.nice}**',
                value=(await self.make_stat_bar(
                    mob.health, mob_max_health,
                    mob_max_health/2,
                    self.d.emojis.heart_full,
                    self.d.emojis.heart_empty
                    )
                )
            )

            msg = await ctx.send(embed=embed)

            try:
                resp = await self.bot.wait_for('message', check=self.attack_check, timeout=15)
            except asyncio.TimeoutError:
                await msg.edit(suppress=True)
                self.d.pause_econ.pop(u.id)

                await self.bot.send('insert random.choice(insults)')
                return

            if resp.content.lower() in ('flee', 'run away'):
                await msg.edit(suppress=True)
                self.d.pause_econ.pop(u.id)

                await self.bot.send('fien, run away leik litul babee')
                return

            u_dmg = await self.calc_sword_damage(u_sword)




    async def spawn_events(self):
        while True:
            await asyncio.sleep(.05)  # don't fucking remove this or else
            for ctx in self.d.spawn_queue:
                self.bot.loop.create_task(self.spawn_event(ctx))  # ah yes eficeicncy

def setup(bot):
    bot.add_cog(Mobs(bot))
