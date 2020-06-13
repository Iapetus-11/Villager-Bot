import asyncio
import discord
from discord.ext import commands
from math import floor, ceil
from random import choice, randint


class MobSpawning(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.g = self.bot.get_cog("Global")
        self.db = self.bot.get_cog("Database")

        self.do_event = []

        self.emerald = "<:emerald:653729877698150405>"

        self.bot.loop.create_task(self.spawn_events())

        # Thank you so much Eun!
        # "mobname": [actualname, health, img_url]
        murl = "http://olimone.ddns.net/images/mob_spawns/"
        self.mobs = {
            "zombie": ["Zombie", 20, murl + "zombie.png"],
            "spider": ["Spider", 16, murl + "spider.png"],
            "skeleton": ["Skeleton", 20, murl + "skeleton.png"],
            "creeper": ["Creeper", 20, murl + "creeper.png"],
            "cave_spider": ["Cave Spider", 12, murl + "cave_spider.png"]
        }

        self.mob_attacks = {
            "zombie": ["The zombie ran lashing at your arms", "The zombie gives you a painful hug",
                       "The zombie punches you in your face!",
                       "The zombie claws you with it's overgrown, decaying nails!",
                       "The zombie punches you with it's decaying hand!"],
            "spider": ["The spider dunks on you", "The spider lunges at you and bites you!",
                       "The spider jumps at you and bites!", "The spider bites you in the leg!"],
            "skeleton": ["The skeleboi yeets an arrow at your face",
                         "The skeleton turns around into a 360 no scopes you!",
                         "An arrow rains from the skeleton, only one", "One headshot from skeleton for you"],
            "creeper": ["You hear a fuse ignite...", "The creeper flashes and fizzles...",
                        "The creeper preps for its imminent suicide..."],
            "cave_spider": ["The cave spider's fangs digs deep onto your skin ",
                            "The cave spider gave you a toxic kiss",
                            "The cave spider bit you and inflicted poison damage!"]
        }

        self.mob_finishers = {
            "zombie": ["The zombie lunges for your throat, and bites!",
                       "The zombie disembowels you and mutilates your remains!"],
            "spider": ["The spider jumps on top of you and bites deep into your skull!"],
            "skeleton": ["The skeleton 360 noscopes you for the last time!",
                         "Arrows rain from the sky, piercing your flesh and killing you!"],
            "creeper": ["The creeper goes boom!", "Creeper used self destruct! *It's super effective!*",
                        "The creeper explodes, yeeting your red, bloodied corpse across the map!",
                        "You were blown to pixels by the creeper!"],
            "cave_spider": ["You died from poison damage!", "The cave spider killed you with poison damage!",
                            "The cave spider killed you with it's venom!"]
        }

        self.drop_msgs = [
            "A wild {0} has found you!", "A vicious {0} has seen you!", "A lurking {0} has seen you!",
            "A lurking {0} has found you!", "A creepy {0} has seen you!", "A creepy {0} has found you!",
            "You have been found by a wild {0}!", "You have been seen by a vicious {0}!",
            "You have been found by a crazy {0}!", "A crazy {0} has seen you!",
            "You ran into a wild {0}!",
            "You ran into a crazy {0}!", "You ran into a {0}!", "You ran into a creepy {0}!",
            "You ran into a vicious {0}!"
        ]

        self.u_attacks = [
            "You slashed the {0} with your {1}!", "Your {1} stabbed deep into the {0}!",
            "You hacked at the {0} with your {1}!", "You swung your {1} at the {0}!",
            "You poked the {0} with your {1}!", "You poked your {1} deep into the {0}!",
            "You hacked pieces off the {0} with your {1}!", "You poked the {0} in the eye with your {1}!",
            "You lunged at the {0} and stabbed it with your {1}!",
            "You charged at the {0} and hacked at it with your {1}!",
            "You charged at the {0} and stabbed it with your {1}!",
            "You charged at the {0} and hacked at it with your {1}!",
            "You charged at the {0} and with all your might poked it with your {1}"
        ]

        self.u_finishers = [
            "You swung the {1} as hard as you could and decapitated the {0}!",
            "You tripped and let go of your {1}, landing it in the {0} and killing it!",
            "You, with all your might, buried the {1} deep into the chest of the {0}!",
            "Slashing your {1} one last time, you banished the {0} from existence!",
            "Swinging your {1} one last time, you slashed the {0} in half!",
            "With one last hack from your {1}, you cut the {0} in half!",
            "With one last swing from your {1}, you banished the {0} from this world!",
            "You hacked at the {0} with all your might, and decapitated it with your {1}!",
            "With the last of your strength, you buried the {1} deep into the chest of the {0}!",
            "Landing the {1} on the neck of the {0}, it finally died!",
            "With the last of your strength, your {1} rips through the {0}!",
            "With the last of your strength, your {1} tears through the {0}!",
            "You hacked with the {1} as hard as you could, and decapitated the {0}!",
            "Missing the {0} with your sword, it died from disappointment..."
        ]

    async def send(self, ctx, m):
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=m))

    async def get_sword(self,
                        uid):  # I'm proud of this # Me 2 weeks later: why the fuck are you proud of this you retarded fuck
        item_names = [item[0].lower() for item in await self.db.get_items(uid)]
        for sword_name in ["netherite sword", "diamond sword", "gold sword", "iron sword", "stone sword", "wood sword"]:
            if sword_name in item_names:
                return sword_name
        await self.db.add_item(uid, "Wood Sword", 1, 0)

    async def calc_sword_damage(self, sword, diff_multi):  # highest sword is used
        if sword == "netherite sword":
            dmg = randint(7, 10)
        elif sword == "diamond sword":
            dmg = randint(6, 7)
        elif sword == "gold sword":
            dmg = randint(4, 5)
        elif sword == "iron sword":
            dmg = randint(2, 4)
        elif sword == "stone sword":
            dmg = randint(1, 3)
        else:
            dmg = randint(1, 2)
        if diff_multi == 2:
            return floor(dmg / 1.25)
        return dmg

    # also have random pillager events where server is ransacked /s
    async def spawn_event(self, ctx):  # Fuck me in the balls, wait don't how is that even possible?!
        self.do_event.pop(self.do_event.index(ctx))  # make sure this motherfucker doesn't get a spawn again

        diff = await self.db.get_difficulty(ctx.guild.id)
        if diff == "peaceful":
            return

        diff_multi = 1
        if diff == "hard":
            diff_multi = 2

        mob_key = choice(list(self.mobs))
        mob = self.mobs[mob_key].copy()  # LMAO I bet there's a better way to do this but fuck it

        mob[1] *= 2

        f_embed = discord.Embed(color=discord.Color.green(), title=f"**{choice(self.drop_msgs).format(mob[0])}**",
                                description="Do you want to ``fight`` the mob?")  # fight it or u little baby piece of shit
        f_embed.set_image(url=mob[2])
        f_msg = await ctx.send(embed=f_embed)
        try:

            def check(m):
                return m.channel == ctx.channel and not m.author.bot and m.content in ["attack", "fight", "punch",
                                                                                       "atk", "atacc", "attacc", "kill",
                                                                                       "fite", "kil", "atak", "atack",
                                                                                       "yes", "yes fight", "yes attack"]

            m = await self.bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await self.send(ctx, "You ran out of time! The mob despawned.")
            await f_msg.edit(suppress=True)
            return

        u = m.author

        if await self.db.get_health(u.id) < 2:
            await self.send(ctx, "You don't have enough health to do this!")

        self.g.pause_econ.append(u.id)

        emeralds_multi = 1
        if await self.db.get_item(u.id, "Looting II") is not None:
            emeralds_multi = 2
        elif await self.db.get_item(u.id, "Looting I") is not None:
            emeralds_multi = 1.5

        h_user = await self.db.get_health(u.id)
        hh = ["<:heart_full:717535027604488243>", "<:heart_empty:717535027319144489>"]

        def check(m):
            return m.author.id == u.id and m.channel.id == ctx.channel.id and (
                    m.content == "flee" or m.content == "attack" or m.content == "atk")

        iter = 0
        while h_user > 0 and mob[1] > 0:
            # h_user = await self.db.get_health(u.id)
            iter += 1
            new_emb = discord.Embed(color=discord.Color.green(), title="Do you want to ``attack`` or ``flee``?")
            new_emb.add_field(name=f"**{u.display_name}**",
                              value="\uFEFF" + await self.db.calc_stat_bar(ceil(h_user / 2), 10, 10, hh[0], hh[1]),
                              inline=False)  # how tf is this gonna work ya retarded cunt
            new_emb.add_field(name=f"**{mob[0]}**",
                              value="\uFEFF" + await self.db.calc_stat_bar(ceil(mob[1] / 2), self.mobs[mob_key][1] / 2,
                                                                           # FUCK THESE LINES OF CODE IN PARTICULAR
                                                                           self.mobs[mob_key][1] / 2, hh[0],
                                                                           # FUCK THESE LINES OF CODE IN PARTICULAR
                                                                           hh[1]),
                              inline=False)  # FUCK THESE LINES OF CODE IN PARTICULAR
            new_emb.set_image(url=mob[2])
            await f_msg.edit(suppress=True)
            f_msg = await ctx.send(embed=new_emb)
            try:
                m = await self.bot.wait_for("message", check=check, timeout=30)
            except asyncio.TimeoutError:
                await f_msg.edit(suppress=True)
                await self.send(ctx,
                                "Ok fine, be that way, ignore me. (The mob despawned waiting for your puny attack)")
                return
            if m.content == "flee":  # Oh you fucking toddler
                await f_msg.edit(suppress=True)
                await self.send(ctx,
                                f"You ran away like {choice(['a little baby', 'a little kid', 'a little baby screaming mommy', 'a whiny little baby', 'the whiny little kid you are'])}.")
                self.g.pause_econ.pop(u.id)
                return

            sword = await self.get_sword(u.id)
            u_dmg = await self.calc_sword_damage(sword, diff_multi)
            mob[1] -= u_dmg

            if mob[1] <= 0:  # player wins
                break

            await ctx.send(
                embed=discord.Embed(color=discord.Color.green(),
                                    description=choice(self.u_attacks).format(mob[0], sword)))

            await asyncio.sleep(1)

            m_dmg = choice([2, 4, 6])
            if mob_key == "creeper":
                if iter > 2:
                    if diff == "easy":
                        if choice([True, False, False]):
                            h_user = 0
                            break
                    else:
                        if choice([True, False]):
                            h_user = 0
                            break
                m_dmg = 0
            h_user -= m_dmg

            if h_user <= 0:  # mob wins
                break

            await ctx.send(
                embed=discord.Embed(color=discord.Color.green(), description=choice(self.mob_attacks[mob_key])))
            await asyncio.sleep(2)

        if h_user > 0:  # PLAYER WIN
            u_bal = await self.db.get_balance(u.id)
            if diff == "easy":
                emeralds_gained = floor(u_bal * (1 / choice([3, 2.25, 3.5, 3.75, 4]))) if u_bal < 1024 else floor(
                    1024 * (1 / choice([3, 2.25, 3.5, 3.75, 4])))
            else:  # diff hard
                emeralds_gained = floor(u_bal * (1 / choice([1.5, 1.75, 2, 2.5]))) if u_bal < 1024 else floor(
                    1024 * (1 / choice([1.5, 1.75, 2, 2.5])))
                emeralds_gained = floor(emeralds_multi * emeralds_gained)
            found = [
                "Wow look at that you found {0}{1} just right there on the ground!",
                "Wow, what's that? {0}{1}!", "You've gained {0}{1}",
                "You've gotten {0}{1}", "You've received {0}{1}"
            ]
            found = choice(found).format(emeralds_gained, self.emerald)
            if emeralds_gained == 0:
                found = "You didn't get anything!"
            await ctx.send(embed=discord.Embed(color=discord.Color.green(),
                                               description=f"You've defeated the {mob[0]}!\n\n{found}"))
            await self.db.set_balance(u.id, u_bal + emeralds_gained)
        else:  # MOB WIN
            u_bal = await self.db.get_balance(u.id)

            if diff == "easy":
                emeralds_lost = floor(u_bal * (1 / choice([2.75, 3, 3.25, 3.5]))) if u_bal > 10 else randint(2, 4)
            else:  # diff hard
                emeralds_lost = floor(u_bal * (1 / choice([1.15, 1.25, 1.35, 1.45]))) if u_bal > 10 else randint(5, 9)

            await self.db.set_balance(u.id, u_bal - emeralds_lost)

            await ctx.send(
                embed=discord.Embed(color=discord.Color.green(), description=choice(self.mob_finishers[mob_key])))
            if emeralds_lost > 0:
                if mob_key == "creeper":
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(),
                                                       description=f"The {mob[0]} also blew up {emeralds_lost}{self.emerald} that were yours..."))
                else:
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(),
                                                       description=f"The {mob[0]} also stole {emeralds_lost}{self.emerald} from you..."))
        # goes at very end yep cleanup idk reeeeee kill me
        del mob
        self.g.pause_econ.pop(u.id)

    async def spawn_events(self):
        while self.bot.is_ready():
            await asyncio.sleep(1)  # idk why this but this?
            await ctx.send("iteration")
            for ctx in self.do_event:  # ah yes efficiency
                self.bot.loop.create_task(self.spawn_event(ctx))  # oh ye bois


def setup(bot):
    bot.add_cog(MobSpawning(bot))
