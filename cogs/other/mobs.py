from discord.ext import commands
import discord


class Mobs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def spawn_event(self, ctx):
        pass

    async def spawn_events(self):
        while True:
            await asyncio.sleep(.05)  # don't fucking remove this or else
            for ctx in self.d.spawn_queue:
                self.bot.loop.create_task(self.spawn_event(ctx))

def setup(bot):
    bot.add_cog(Mobs(bot))
