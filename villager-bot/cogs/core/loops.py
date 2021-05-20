from discord.ext import commands, tasks
from classyjson import ClassyDict

class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ipc = bot.ipc

        self.handle_broadcasts.start()

    def cog_unload(self):
        self.handle_broadcasts.stop()

    async def handle_packet(self, packet: ClassyDict) -> None:
        if packet.type == "eval":
            try:
                result = eval(packet.code, self.eval_env)
                success = True
            except Exception as e:
                result = str(e)
                success = False

            await self.ipc.send({"type": "eval-response", "id": packet.id, "result": result, "success": success})

    @tasks.loop(seconds=.5)
    async def handle_unexpected_packets(self):
        await asyncio.gather(*map(self.handle_packet, self.ipc.unexpected_packets))


def setup(bot):
    bot.add_cog(Loops(bot))
