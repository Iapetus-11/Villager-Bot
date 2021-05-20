from classyjson import ClassyDict
from discord.ext import commands
import aiohttp
import asyncio
import time

from util.setup import villager_bot_intents, setup_logging, setup_database
from util.setup import load_text, load_secrets, load_data
from util.ipc import Client


def run_shard(shard_count: int, shard_ids: list) -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())

    shard_group = VillagerBotShardGroup(shard_count, shard_ids)
    shard_group.run()


class VillagerBotShardGroup(commands.AutoShardedBot):
    def __init__(self, shard_count: int, shard_ids: list) -> None:
        super().__init__(
            command_prefix="!!",
            intents=villager_bot_intents(),
            shard_count=shard_count,
            shard_ids=shard_ids,
        )

        self.start_time = time.time()

        self.k = load_secrets()
        self.d = load_data()
        self.l = load_text()

        self.cog_list = [
            "cogs.core.events",
        ]

        self.logger = setup_logging(self.shard_ids)
        self.ipc = Client(self.k.manager.host, self.k.manager.port, self.k.manager.auth)
        self.aiohttp = aiohttp.ClientSession()
        self.db = None

    async def start(self, *args, **kwargs):
        await self.ipc.connect(self.shard_ids)
        self.db = await setup_database(self.k)

        for cog in self.cog_list:
            self.load_extension(cog)

        await super().start(*args, **kwargs)

    async def close(self, *args, **kwargs):
        await self.ipc.close()
        await self.db.close()
        await self.aiohttp.close()

        await super().close(*args, **kwargs)

    def run(self, *args, **kwargs):
        super().run(self.k.discord_token, *args, **kwargs)
