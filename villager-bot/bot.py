from classyjson import ClassyDict
from discord.ext import commands
import aiohttp
import asyncio

from util.setup import villager_bot_intents, setup_logging, setup_database
from util.setup import load_text, load_secrets, load_data
from util.ipc import Client


def run_shard(shard_count: int, shard_id: int) -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())

    shard = VillagerBotShard(shard_count, shard_id)
    shard.run(secrets.discord_token)


class VillagerBotShard(commands.Bot):
    def __init__(self, shard_count: int, shard_id: int, *, secrets: ClassyDict, data: ClassyDict, text: ClassyDict) -> None:
        super().__init__(
            command_prefix="!!",
            intents=villager_bot_intents(),
            shard_count=shard_count,
            shard_id=shard_id,
        )

        self.k = load_secrets()
        self.d = load_data()
        self.l = load_text()

        self.ipc = Client()

        self.cog_list = [
            "cogs.core.events",
        ]

        for cog in self.cog_list:
            self.load_extension(cog)

    def run(self):
        super().run(self.k.discord_token)
