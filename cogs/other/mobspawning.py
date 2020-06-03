from discord.ext import commands
import discord
from random import choice, randint
import asyncio


class MobSpawning(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.db = self.bot.get_cog("Database")

        self.do_event = []

        # "mobname": [actualname, health, ]
        murl = "http://olimone.ddns.net/images/mob_spawns/"
        self.mobs = {"zombie": ["Zombie", 20, murl+"zombie.png"], "spider": ["Spider", 16, murl+"spider.png"], "skeleton": ["Skeleton", 20, murl+"skeleton.png"],
                     "creeper": ["Creeper", 20, murl+"creeper.png"], "cave_spider": ["Cave Spider", 12, murl+"cave_spider.png"]}

        self.drop_msgs = ["A wild {0} has found you!", "A vicious {0} has seen you!", "A lurking {0} has seen you!",
                          "A lurking {0} has found you!", "A creepy {0} has seen you!", "A creepy {0} has found you!",
                          "You have been found by a wild {0}!", "You have been seen by a vicious {0}!",
                          "You have been found by a crazy {0}!", "A crazy {0} has seen you!"]

    # also have random pillager events where server is ransacked /s
    async def spawn_event(self, ctx): # Fuck me in the balls, wait don't how is that even possible?!
        #self.do_event.pop(self.do_event.index(ctx)) # make sure this motherfucker doesn't get a spawn again

        diff = await self.db.get_difficulty(ctx.guild.id)
        if diff == "peaceful":
            return

        mob_key = choice(list(self.mobs))
        mob = self.mobs[mob_key] # LMAO I bet there's a better way to do this but fuck it

        f_embed = discord.Embed(color=discord.Color.green(), title="**"+choice(self.drop_msgs).format(mob[0])+"**", description="Do you want to ``fight`` the mob or ``flee``?") # fight it or u little baby
        f_embed.set_image(url=mob[2])
        f_msg = await ctx.send(embed=f_embed)
        try:
            def check(m):
                return m.channel == ctx.channel and not m.author.bot and ("fight" == m.content or "flee" == m.content)
            m = await self.bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            try:
                await f_msg.delete()
            except Exception:
                pass
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You ran out of time! The mob despawned."))
            return
        if m.content == "flee": # That's right you whiny little shit
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"You ran away like {choice(['a little baby', 'a little kid','a little baby screaming mommy', 'a whiny little baby', 'the whiny little kid you are'])}."))
            return

        u = m.author
        h_user = await self.db.get_health(u.id)
        hh = ["<:heart_full:717535027604488243>", "<:heart_empty:717535027319144489>"]

        def check(m):
            return m.author.id == u.id and m.channel.id == ctx.channel.id

        while h_user > 0 and mob[1] > 0:
            h_user = await self.db.get_health(u.id)
            new_emb = discord.Embed(color=discord.Color.green(), title="Do you want to ``attack`` or ``flee``?")
            new_emb.add_field(name=f"**{u.display_name}**", value=await self.db.calc_stat_bar(h_user, 20, 10, hh[0], hh[1]), inline=False) # how tf is this gonna work ya retarded cunt
            new_emb.add_field(name=f"**{mob[0]}**", value=await self.db.calc_stat_bar(mob[1], self.mobs[mob_key][1], self.mobs[mob_key][1]/2, hh[0], hh[1]), inline=False)
            new_emb.set_image(url=mob[2])
            await f_msg.edit(suppress=True)
            f_msg = await ctx.send(embed=new_emb)
            try:
                m = await self.bot.wait_for("message", check=check, timeout=30)
            except asyncio.TimeoutError:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Ok fine, be that way, ignore me. (Timed out waiting for a response)"))
                return
            if m.content == "flee": # Oh you fucking toddler
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"You ran away like {choice(['a little baby', 'a little kid','a little baby screaming mommy', 'a whiny little baby', 'the whiny little kid you are'])}."))
                return
            user_sword = await self.db.get_sword(u.id) # Implement this retard

    @commands.Cog.listener()
    async def on_ready(self):
        while self.bot.is_ready():
            asyncio.sleep(.05) # idk why this but this?
            for ctx in self.do_event: # ah yes efficiency
                await self.spawn_event(ctx)


def setup(bot):
    bot.add_cog(MobSpawning(bot))
