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

        if await self.db.get_difficulty(ctx.guild.id) == "peaceful":
            return

        mob = self.mobs[choice(list(self.mobs))] # LMAO I bet there's a better way to do this but fuck it

        f_embed = discord.Embed(color=discord.Color.green(), title="**"+choice(self.drop_msgs).format(mob[0])+"**", description="Type ``fight`` or ``flee``")
        f_embed.set_image(url=mob[2])
        f_msg = await ctx.send(embed=f_embed)
        try:
            def check(m):
                return m.channel == ctx.channel and not m.author.bot and ("fight" == m.content or "flee" == m.content)
            await self.bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            try:
                await f_msg.delete()
            except Exception:
                pass
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You ran out of time! The mob despawned."))
            return
        if m.content == "flee":
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"You ran away like {choice('a little baby', 'a little kid', 'a little baby screaming mommy')}."))
            return

    @commands.Cog.listener()
    async def on_ready(self):
        while self.bot.is_ready():
            asyncio.sleep(.05) # idk why this but this?
            for ctx in self.do_event:
                await self.spawn_event(ctx)


def setup(bot):
    bot.add_cog(MobSpawning(bot))
