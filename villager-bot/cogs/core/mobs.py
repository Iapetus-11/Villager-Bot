from discord.ext import commands
import random
import math


class MobSpawner:
    def __init__(self, bot):
        self.bot = bot

        self.d = bot.d
        self.db = bot.get_cog("Database")

    def engage_check(self, ctx):
        async def predicate(m):
            if (await self.ipc.eval(f"econ_paused_users.get({ctx.author.id})")).result is not None:
                return False

            if m.content.lower().lstrip(ctx.prefix) not in self.d.mobs_mech.valid_attacks:
                return False

            return m.channel == ctx.channel and not ctx.author.bot and ctx.author.id not in self.bot.ban_cache

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

    async def calculate_sword_damage(self, uid: int, sword: str, multi: float) -> int:
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

        if await self.db.fetch_item(uid, "Sharpness II Book") is not None:
            damage *= 1.5
        elif await self.db.fetch_item(uid, "Sharpness I Book") is not None:
            damage *= 1.25

        if multi > 1:
            damage /= 1.3

        return math.ceil(damage)


def setup(bot):
    bot.add_cog(MobSpawner(bot))
