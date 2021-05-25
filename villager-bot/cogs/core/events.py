from discord.ext import commands
import time


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_shard_ready(self, shard_id: int):
        await self.bot.ipc.send({"type": "shard-ready", "shard_id": shard_id})
        self.bot.logger.info(f"Shard {shard_id} \u001b[36;1mREADY\u001b[0m")

        # packet = await self.bot.ipc.request({"type": "eval", "code": "v.start_time"})
        # self.bot.logger.info(f"Shard {shard_id} received response {packet}")

    @commands.Cog.listener()
    async def on_shard_disconnect(self, shard_id: int):
        await self.bot.ipc.send({"type": "shard-disconnect", "shard_id": shard_id})

    @commands.Cog.listener()
    async def on_command_error(self, ctx, e):
        if hasattr(ctx, "custom_error"):
            pass

        if isinstance(e, commands.CommandOnCooldown):
            pass


def setup(bot):
    bot.add_cog(Events(bot))
