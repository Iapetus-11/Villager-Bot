from discord.ext import commands, tasks
from classyjson import ClassyDict
import asyncio


class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ipc = bot.ipc

        self.handle_unexpected_packets.start()

    def cog_unload(self):
        self.handle_unexpected_packets.stop()

    async def handle_packet(self, packet: ClassyDict) -> None:
        if packet.type == "eval":
            try:
                result = eval(packet.code, self.eval_env)
                success = True
            except Exception as e:
                result = str(e)
                success = False

            await self.ipc.send({"type": "broadcast-response", "id": packet.id, "result": result, "success": success})

    @tasks.loop(seconds=0.5)
    async def handle_unexpected_packets(self):
        unexpected_packets = self.ipc.unexpected_packets.copy()
        self.ipc.unexpected_packets.clear()

        await asyncio.gather(*map(self.handle_packet, unexpected_packets))

    @handle_unexpected_packets.before_loop
    async def before_handle_unexpected_packets(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Loops(bot))
