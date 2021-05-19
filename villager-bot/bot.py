from classyjson import ClassyDict
from discord.ext import commands
import aiohttp
import asyncio

from util.setup import villager_bot_intents, setup_logging, setup_database
from util.setup import load_text, load_secrets, load_data
from util.ipc import Client


def run_shard(shard_count: int, shard_id: int) -> None:
    secrets, data, text = load_secrets(), load_data(), load_text()
    shard = VillagerBotShard(shard_count, shard_id, secrets, data, text)

    try:
        asyncio.run(shard.start())
    finally:
        asyncio.run(shard.stop())


class VillagerBotShard:
    def __init__(self, shard_count: int, shard_id: int, secrets: ClassyDict, data: ClassyDict, text: ClassyDict) -> None:
        self.shard_count = shard_count
        self.shard_id = shard_id

        self.k = secrets
        self.d = data
        self.l = text

        self.logger = setup_logging(shard_id)
        self.aiohttp = None
        self.db = None

        self.bot = commands.Bot(
            command_prefix=self.get_prefix,
            intents=villager_bot_intents(),
            shard_count=shard_count,
            shard_id=shard_id,
        )

        self.ipc = Client(
            secrets.manager.host,  # ip manager is hosted on
            secrets.manager.port,  # port manager is hosted on
            secrets.manager.auth,  # auth which is passed with every packet
        )

    async def start(self):
        self.aiohttp = aiohttp.ClientSession()
        self.db = await setup_database(self.k)

        await self.ipc.connect(self.shard_id)  # connect to manager server
        await self.db  # connect to database

        await self.bot.start(self.k.discord_token)  # run bot

    async def stop(self):
        await self.bot.close()  # close connection to discord gateway
        await self.aiohttp.close()  # close aiohttp ClientSession
        await self.db.close()  # close connections in db pool
        await self.ipc.close()  # close connection to manager

    async def get_prefix(self):
        return self.d.default_prefix
