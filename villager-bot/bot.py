from classyjson import ClassyDict
from discord.ext import commands
import aiohttp
import asyncio

from util.setup import villager_bot_intents, setup_logging, setup_database
from util.ipc import Client

def run_shard(shard_count: int, shard_id: int, secrets: ClassyDict, data: ClassyDict, text: ClassyDict) -> None:
    shard = VillagerBotShard(shard_count, shard_id, secrets, data, text)

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(shard.run())
    except KeyboardInterrupt:
        loop.run_until_complete(shard.stop())


class VillagerBotShard:
    def __init__(self, shard_count: int, shard_id: int, secrets: ClassyDict, data: ClassyDict, text: ClassyDict) -> None:
        self.shard_count = shard_count
        self.shard_id = shard_id

        self.k = secrets
        self.d = data
        self.l = text

        self.aiohttp = aiohttp.ClientSession()
        self.logger = setup_logging(shard_id)
        self.db = setup_database(secrets)

        self.bot = commands.Bot(
            shard_count=shard_count,
            shard_id=shard_id,
            prefix=self.get_prefix,
            intents=villager_bot_intents(),
        )

        self.ipc = Client(
            secrets.manager.host, # ip manager is hosted on
            secrets.manager.port, # port manager is hosted on
            secrets.manager.auth, # auth which is passed with every packet
        )

    async def run(self):
        await self.ipc.connect(self.shard_id)  # connect to manager server
        await self.db  # connect to database
        await self.bot.start()  # run bot

    async def stop(self):
        await self.ipc.close()  # close connection to manager
        await self.db.close()  # close connections in db pool
        await self.bot.close()  # close connection to discord gateway
