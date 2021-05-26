from discord.ext import commands


class Share(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ipc = bot.ipc

    async def __getitem__(self, key: str) -> object:
        return await self.ipc.request({"type": "eval", "code": key})

    async def __setitem__(self, key: str, value: object) -> None:
        await self.ipc.request({"type": "exec", "code": f"{key} = {value}"})


def setup(bot):
    bot.add_cog(Share(bot))
