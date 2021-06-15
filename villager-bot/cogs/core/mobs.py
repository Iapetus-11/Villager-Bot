from discord.ext import commands


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

            return m.channel.id == ctx.channel.id and not ctx.author.bot and ctx.author.id not in self.bot.ban_cache

        return commands.check(predicate)


def setup(bot):
    bot.add_cog(MobSpawner(bot))
