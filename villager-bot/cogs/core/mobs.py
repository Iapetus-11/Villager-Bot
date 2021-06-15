from discord.ext import commands


class MobSpawner:
    def __init__(self, bot):
        self.bot = bot

        self.d = bot.d
        self.db = bot.get_cog("Database")
    
    def engage_check(self, m, ctx):
        if self.v.pause_econ.get(m.author.id):
            return False

        if m.content.lower().replace(ctx.prefix, "", 1) not in self.d.mobs_mech.valid_attacks:
            return False

        return m.channel.id == ctx.channel.id and not u.bot and u.id not in self.v.ban_cache

    def engage_check(self, ctx):
        async def predicate(m):
            if (await self.ipc.eval(f"econ_paused_users.get({ctx.author.id})")).result is not None:
                return False

        return commands.check(predicate)
    

def setup(bot):
    bot.add_cog(MobSpawner(bot))