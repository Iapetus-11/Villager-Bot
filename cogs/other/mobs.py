from discord.ext import commands
import discord
import random
import math


class Mobs(commands.Cog):  # fuck I really don't want to work on this
    def __init__(self, bot):
        self.bot = bot
        self.d = self.bot.d

        self.db = self.bot.get_cog('Database')

        self.bot.loop.create_task(self.spawn_events())

    def first_time_check(self, m, ctx):
        u = m.author

        if m.content not in self.d.mobs_mech.valid_attacks:
            return False

        return m.channel.id == ctx.channel.id and not u.bot and u.id not in self.d.ban_cache and u.id not in self.d.pause_econ

    def regular_check(self, m, ctx):
        pass

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

        if diff_multi > 1:
            dmg = dmg / 1.3

        if await self.db.fetch_item(uid, 'Sharpness II Book') is not None:
            dmg *= 1.5
        elif await self.db.fetch_item(uid, 'Sharpness I Book') is not None:
            dmg *= 1.25

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
            

    async def spawn_events(self):
        while True:
            await asyncio.sleep(.05)  # don't fucking remove this or else
            for ctx in self.d.spawn_queue:
                self.bot.loop.create_task(self.spawn_event(ctx))  # ah yes eficeicncy

def setup(bot):
    bot.add_cog(Mobs(bot))
